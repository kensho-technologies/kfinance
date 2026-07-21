from datetime import date
from textwrap import dedent
from typing import Type

import httpx
from pydantic import BaseModel, Field

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.mergers_and_acquisitions.merger_and_acquisition_models import (
    MergersInfo,
    MergersResp,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithIdInfoAndErrors,
)


class GetMergersFromIdentifiersArgs(ToolArgsWithIdentifiers):
    start_date: date | None = Field(
        description="The start date for merger date-range filtering. Use null for all mergers.",
        default=None,
    )
    end_date: date | None = Field(
        description="The end date for merger date-range filtering. Use null for all mergers.",
        default=None,
    )


class GetMergersFromIdentifiersResp(ToolRespWithIdInfoAndErrors[MergersResp]):
    pass


class GetMergersFromIdentifiers(KfinanceTool):
    name: str = "get_mergers_from_identifiers"
    description: str = dedent("""
        Retrieves all merger and acquisition transactions involving the specified company. This is the entry point for ALL M&A questions: it maps a company to its transactions.

        If a start_date and/or end_date is specified, only mergers where the merger
        timeline intersects with the date range are returned. The merger timeline is
        considered to be from the earliest event associated with the merger to
        the latest event. If any date between (and inclusive of) these two event dates
        falls within the passed-in date range, the merger is returned. If only an
        announcement date is found for a merger, the merger timeline is taken to be
        until the earlier of the current date or 10 years after the announcement date.

        Results are categorized by the company's role: target (being acquired), buyer (making the acquisition), or seller (divesting an asset).

        This tool returns ONLY transaction_id, status, start_date, closed_date, target, and buyers for each transaction. It does NOT return deal/transaction values, amounts paid, or participant details. To get any of those, take all relevant transaction_ids from this responses and call get_mergers_info_from_transaction_ids with them.

        - The numeric identifier of a COMPANY is never a transaction_id. Always obtain transaction_id values from this tool's response — never pass a company identifier to get_mergers_info_from_transaction_ids.
        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - When requesting all mergers, leave start_date and end_date null.
        - Only specify date ranges when the user explicitly requests mergers and acquisitions during some date range.
        - Provides transaction_id, status, start_date, closed_date, target, and buyers.

        Examples:
        Query: "Which companies did Microsoft purchase?"
        Function: get_mergers_from_identifiers(identifiers=["Microsoft"])

        Query: "Get acquisitions for AAPL and GOOGL"
        Function: get_mergers_from_identifiers(identifiers=["AAPL", "GOOGL"])

        Query: "What companies was Apple selling between 2019 and 2022?"
        Function: get_mergers_from_identifiers(identifiers=["Apple"], start_date="2019-01-01", end_date="2022-12-31")
    """).strip()
    args_schema: Type[BaseModel] = GetMergersFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    async def _arun(
        self, identifiers: list[str], start_date: date | None = None, end_date: date | None = None
    ) -> GetMergersFromIdentifiersResp:
        """"""
        return await get_mergers_from_identifiers(
            identifiers=identifiers,
            start_date=start_date,
            end_date=end_date,
            httpx_client=self.kfinance_client.httpx_client,
        )


class GetMergersInfoFromTransactionIdsArgs(BaseModel):
    transaction_ids: list[int] = Field(description="The IDs of the transactions.")
    include_advisors: bool = Field(
        default=False, description="Whether to include advisors for participants in the response"
    )
    include_comments: bool = Field(
        default=False, description="Whether to include transaction comments in the response"
    )


class GetMergersInfoFromTransactionIds(KfinanceTool):
    name: str = "get_mergers_info_from_transaction_ids"
    description: str = dedent("""
        Provides comprehensive information about merger or acquisition transactions, including their timeline (announced date, closed date), participants' company_names, company_ids, and advisors if advisors are requested (participants are categorized as target, buyers, sellers), and financial consideration details (including monetary values).

        Use this tool for questions about announcement dates, deal/transaction values or amounts paid, completion status, and transaction details.

        The transaction_ids MUST come from get_mergers_from_identifiers responses. They are NOT company_ids or tickers. If you have not yet called get_mergers_from_identifiers for the company in question, do that first.

        When a question concerns more than one transaction (e.g. "all acquisitions over $5B", "deals since 2020"), call this tool and pass in EVERY transaction_id from the get_mergers_from_identifiers response that matches the criteria — not just the first one.

        Examples:
        Query: "When was the acquisition of Ben & Jerry's announced?"
        Function 1: get_mergers_from_identifiers(identifiers=["Ben & Jerry's"])
        # Function 1 returns all M&A's that involved Ben & Jerry's. Extract the <transaction_id> from the response where Ben & Jerry's was the target.
        Function 2: get_mergers_info_from_transaction_ids(transaction_ids=[<transaction_id>])

        Query: "What was the transaction size of Vodafone's acquisition of Mannesmann?"
        Function 1: get_mergers_from_identifiers(identifiers=["Vodafone"])
        # Function 1 returns all M&A's that involved Vodafone. Extract the <transaction_id> from the response where Vodafone was the buyer and Mannesmann was the target.
        Function 2: get_mergers_info_from_transaction_ids(transaction_ids=[<transaction_id>])

        Query: "List Microsoft's acquisitions over $5 billion announced since 2020, along with the advisors and comments for the acquisitions."
        Function 1: get_mergers_from_identifiers(identifiers=["Microsoft"], start_date="2020-01-01")
        # Function 1 returns transactions where Microsoft was the buyer, each with a transaction_id. Deal value and announcement date are NOT in that response, so call get_mergers_info_from_transaction_ids, passing in EVERY candidate transaction_id to check the $5B threshold, the announcement date, advisors, and comments.
        Function 2: get_mergers_info_from_transaction_ids(transaction_ids=[<transaction_id_1>, <transaction_id_2>, <transaction_id_3>], include_advisors=True, include_comments=True)
    """).strip()
    args_schema: Type[BaseModel] = GetMergersInfoFromTransactionIdsArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    async def _arun(
        self,
        transaction_ids: list[int],
        include_advisors: bool = False,
        include_comments: bool = False,
    ) -> MergersInfo:
        """"""
        return await get_mergers_info_from_transaction_ids(
            transaction_ids=transaction_ids,
            include_advisors=include_advisors,
            include_comments=include_comments,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def get_mergers_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
    start_date: date | None = None,
    end_date: date | None = None,
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
                start_date=start_date,
                end_date=end_date,
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

    return GetMergersFromIdentifiersResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
    )


async def fetch_mergers_from_company_id(
    company_id: int,
    httpx_client: httpx.AsyncClient,
    start_date: date | None = None,
    end_date: date | None = None,
) -> MergersResp:
    """Fetch mergers for one company_id."""
    start_date_str = start_date.isoformat() if start_date else "none"
    end_date_str = end_date.isoformat() if end_date else "none"

    url = f"/mergers/{company_id}/{start_date_str}/{end_date_str}"
    resp = await httpx_client.get(url=url)
    resp.raise_for_status()
    return MergersResp.model_validate(resp.json())


async def get_mergers_info_from_transaction_ids(
    transaction_ids: list[int],
    include_advisors: bool,
    include_comments: bool,
    httpx_client: httpx.AsyncClient,
) -> MergersInfo:
    """Fetch detailed merger info for a transaction ID."""
    resp = await httpx_client.post(
        url="/mergers/info",
        json={
            "transaction_ids": transaction_ids,
            "include_advisors": include_advisors,
            "include_comments": include_comments,
        },
    )
    resp.raise_for_status()
    return MergersInfo.model_validate(resp.json())
