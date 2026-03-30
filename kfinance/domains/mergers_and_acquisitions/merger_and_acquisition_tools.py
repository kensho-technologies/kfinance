from textwrap import dedent
from typing import Type

import httpx
from pydantic import BaseModel, Field

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.mergers_and_acquisitions.merger_and_acquisition_models import (
    AdvisorResp,
    MergerInfo,
    MergersResp,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifier,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
)


class GetMergersFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, MergersResp]


class GetMergersFromIdentifiers(KfinanceTool):
    name: str = "get_mergers_from_identifiers"
    description: str = dedent("""
        Retrieves all merger and acquisition transactions involving the specified company.

        Results are categorized by the company's role: target (being acquired), buyer (making the acquisition), or seller (divesting an asset).

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - Provides transaction_id, merger_title, and transaction closed_date.

        Examples:
        Query: "Which companies did Microsoft purchase?"
        Function: get_mergers_from_identifiers(identifiers=["Microsoft"])

        Query: "Get acquisitions for AAPL and GOOGL"
        Function: get_mergers_from_identifiers(identifiers=["AAPL", "GOOGL"])
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    async def _arun(self, identifiers: list[str]) -> GetMergersFromIdentifiersResp:
        """"""
        return await get_mergers_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
        )


class GetMergerInfoFromTransactionIdArgs(BaseModel):
    transaction_id: int | None = Field(description="The ID of the transaction.")


class GetMergerInfoFromTransactionId(KfinanceTool):
    name: str = "get_merger_info_from_transaction_id"
    description: str = dedent("""
        Provides comprehensive information about a specific merger or acquisition transaction, including its timeline (announced date, closed date), participants' company_name and company_id (target, buyers, sellers), and financial consideration details (including monetary values).

        Use this tool for questions about announcement dates and transaction details.

        Examples:
        Query: "When was the acquisition of Ben & Jerry's announced?"
        Function 1: get_mergers_from_identifiers(identifiers=["Ben & Jerry's"])
        # Function 1 returns all M&A's that involved Ben & Jerry's. Extract the <key_dev_id> from the response where Ben & Jerry's was the target.
        Function 2: get_merger_info_from_transaction_id(transaction_id=<key_dev_id>)

        Query: "What was the transaction size of Vodafone's acquisition of Mannesmann?"
        Function 1: get_mergers_from_identifiers(identifiers=["Vodafone"])
        # Function 1 returns all M&A's that involved Vodafone. Extract the <key_dev_id> from the response where Vodafone was the buyer and Mannesmann was the target.
        Function 2: get_merger_info_from_transaction_id(transaction_id=<key_dev_id>)


    """).strip()
    args_schema: Type[BaseModel] = GetMergerInfoFromTransactionIdArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    async def _arun(self, transaction_id: int) -> MergerInfo:
        """"""
        return await get_merger_info_from_transaction_id(
            transaction_id=transaction_id,
            httpx_client=self.kfinance_client.httpx_client,
        )


class GetAdvisorsForCompanyInTransactionFromIdentifierArgs(ToolArgsWithIdentifier):
    transaction_id: int | None = Field(description="The ID of the merger.")


class GetAdvisorsForCompanyInTransactionFromIdentifierResp(ToolRespWithErrors):
    results: list[AdvisorResp]


class GetAdvisorsForCompanyInTransactionFromIdentifier(KfinanceTool):
    name: str = "get_advisors_for_company_in_transaction"
    description: str = dedent("""
        Returns a list of advisor companies that provided advisory services to the specified company during a particular merger or acquisition transaction.

        Examples:
        Query: "Who advised S&P Global during their purchase of Kensho?"
        Function 1: get_mergers_from_identifiers(identifiers=["S&P Global"])
        # Function 1 returns all M&A's that involved S&P Global. Extract the <key_dev_id> from the response where S&P Global was the buyer and Kensho was the target.
        Function 2: get_advisors_for_company_in_transaction(identifier="S&P Global", transaction_id=<key_dev_id>)

        Query: "Which firms advised AAPL in transaction 67890?"
        Function: get_advisors_for_company_in_transaction(identifier="AAPL", transaction_id=67890)
    """).strip()
    args_schema: Type[BaseModel] = GetAdvisorsForCompanyInTransactionFromIdentifierArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    async def _arun(
        self, identifier: str, transaction_id: int
    ) -> GetAdvisorsForCompanyInTransactionFromIdentifierResp:
        """"""
        return await get_advisors_for_company_in_transaction_from_identifier(
            identifier=identifier,
            transaction_id=transaction_id,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def get_mergers_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
) -> GetMergersFromIdentifiersResp:
    """Fetch mergers for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_mergers_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                httpx_client=httpx_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, MergersResp] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            results[task.result_key] = task.result

    return GetMergersFromIdentifiersResp(results=results, errors=errors)


async def fetch_mergers_from_company_id(
    company_id: int,
    httpx_client: httpx.AsyncClient,
) -> MergersResp:
    """Fetch mergers for one company_id."""
    url = f"/mergers/{company_id}"
    resp = await httpx_client.get(url=url)
    resp.raise_for_status()
    return MergersResp.model_validate(resp.json())


async def get_merger_info_from_transaction_id(
    transaction_id: int,
    httpx_client: httpx.AsyncClient,
) -> MergerInfo:
    """Fetch detailed merger info for a transaction ID."""
    url = f"/merger/info/{transaction_id}"
    resp = await httpx_client.get(url=url)
    resp.raise_for_status()
    return MergerInfo.model_validate(resp.json())


async def get_advisors_for_company_in_transaction_from_identifier(
    identifier: str,
    transaction_id: int,
    httpx_client: httpx.AsyncClient,
) -> GetAdvisorsForCompanyInTransactionFromIdentifierResp:
    """Fetch advisors for a company in a specific transaction."""

    # First resolve the identifier to company ID
    id_triple_resp = await unified_fetch_id_triples(
        identifiers=[identifier], httpx_client=httpx_client
    )

    # If the identifier cannot be resolved, return the associated error
    if id_triple_resp.errors:
        return GetAdvisorsForCompanyInTransactionFromIdentifierResp(
            results=[], errors=list(id_triple_resp.errors.values())
        )

    id_triple = id_triple_resp.identifiers_to_id_triples[identifier]
    company_id = id_triple.company_id

    # Fetch advisors for this company in the transaction
    url = f"/merger/info/{transaction_id}/advisors/{company_id}"
    resp = await httpx_client.get(url=url)
    response_data = resp.json()

    advisors_response: list[AdvisorResp] = []
    if "advisors" in response_data and response_data["advisors"]:
        for advisor in response_data["advisors"]:
            advisors_response.append(
                AdvisorResp(
                    advisor_company_id=advisor["advisor_company_id"],
                    advisor_company_name=advisor["advisor_company_name"],
                    advisor_type_name=advisor["advisor_type_name"],
                )
            )

    return GetAdvisorsForCompanyInTransactionFromIdentifierResp(
        results=advisors_response, errors=[]
    )
