from textwrap import dedent
from typing import Type

import httpx
from pydantic import BaseModel, Field

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.earnings.earning_models import EarningsCall, EarningsCallResp
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
)


class GetTranscriptFromKeyDevIdArgs(BaseModel):
    """Tool argument with a key_dev_id."""

    key_dev_id: int = Field(description="The key_dev_id for the earnings call")


class GetTranscriptFromKeyDevIdResp(BaseModel):
    transcript: str


class GetTranscriptFromKeyDevId(KfinanceTool):
    name: str = "get_transcript_from_key_dev_id"
    description: str = dedent("""
        Get the raw transcript text for an earnings call by key_dev_id.

        The key_dev_id is obtained from earnings tools (get_earnings_from_identifiers, get_latest_earnings_from_identifiers, or get_next_earnings_from_identifiers).

        Example:
        Query: "Get the transcript for earnings call 12346"
        Function: get_transcript_from_key_dev_id(key_dev_id=12346)
    """).strip()
    args_schema: Type[BaseModel] = GetTranscriptFromKeyDevIdArgs
    accepted_permissions: set[Permission] | None = {Permission.TranscriptsPermission}

    async def _arun(self, key_dev_id: int) -> GetTranscriptFromKeyDevIdResp:
        """"""
        transcript = await get_transcript_from_key_dev_id(
            key_dev_id=key_dev_id,
            httpx_client=self.kfinance_client.httpx_client,
        )
        return GetTranscriptFromKeyDevIdResp(transcript=transcript)


class GetEarningsFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, EarningsCallResp]


class GetNextOrLatestEarningsFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, EarningsCall]


class GetEarningsFromIdentifiers(KfinanceTool):
    name: str = "get_earnings_from_identifiers"
    description: str = dedent("""
        Get all earnings calls for a list of identifiers.

        Returns a list of dictionaries with 'name' (str), 'key_dev_id' (int), and 'datetime' (str in ISO 8601 format with UTC timezone) attributes for each identifier.

        - Use get_latest_earnings_from_identifiers to get only the most recent earnings
        - Use get_next_earnings_from_identifiers to get only the next upcoming earnings
        - To fetch the full transcript, call get_transcript_from_key_dev_id with the key_dev_id

        Examples:
        Query: "Get all earnings calls for Microsoft"
        Function: get_earnings_from_identifiers(identifiers=["Microsoft"])

        Query: "Get earnings for CRM and ORCL"
        Function: get_earnings_from_identifiers(identifiers=["CRM", "ORCL"])
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {
        Permission.EarningsPermission,
        Permission.TranscriptsPermission,
    }

    async def _arun(self, identifiers: list[str]) -> GetEarningsFromIdentifiersResp:
        """"""
        return await get_earnings_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
        )


class GetLatestEarningsFromIdentifiers(KfinanceTool):
    name: str = "get_latest_earnings_from_identifiers"
    description: str = dedent("""
        Get the latest (most recent) earnings call for a list of identifiers.

        Returns a dictionary with 'name' (str), 'key_dev_id' (int), and 'datetime' (str in ISO 8601 format with UTC timezone) attributes for each identifier.

        - Use get_earnings_from_identifiers for all historical earnings
        - Use get_next_earnings_from_identifiers for upcoming earnings
        - To fetch the full transcript, call get_transcript_from_key_dev_id with the key_dev_id

        Examples:
        Query: "What was Microsoft's latest earnings call?"
        Function: get_latest_earnings_from_identifiers(identifiers=["Microsoft"])

        Query: "Get latest earnings for JPM and GS"
        Function: get_latest_earnings_from_identifiers(identifiers=["JPM", "GS"])
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {
        Permission.EarningsPermission,
        Permission.TranscriptsPermission,
    }

    async def _arun(self, identifiers: list[str]) -> GetNextOrLatestEarningsFromIdentifiersResp:
        """"""
        earnings_responses = await get_earnings_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
        )
        output_model = GetNextOrLatestEarningsFromIdentifiersResp(results=dict(), errors=list())
        for identifier, earnings in earnings_responses.results.items():
            most_recent_earnings = earnings.most_recent_earnings
            if most_recent_earnings:
                output_model.results[identifier] = most_recent_earnings
            else:
                output_model.errors.append(f"No latest earnings available for {identifier}.")
        # Add errors from the earnings fetch
        output_model.errors.extend(earnings_responses.errors)
        return output_model


class GetNextEarningsFromIdentifiers(KfinanceTool):
    name: str = "get_next_earnings_from_identifiers"
    description: str = dedent("""
        Get the next scheduled earnings call for a list of identifiers.

        Returns a dictionary with 'name' (str), 'key_dev_id' (int), and 'datetime' (str in ISO 8601 format with UTC timezone) attributes for each identifier.

        - Use get_latest_earnings_from_identifiers for the most recent completed earnings
        - Use get_earnings_from_identifiers for all historical earnings
        - To fetch the full transcript (once available), call get_transcript_from_key_dev_id with the key_dev_id

        Examples:
        Query: "When is Waste Management's next earnings call?"
        Function: get_next_earnings_from_identifiers(identifiers=["Waste Management"])

        Query: "Get next earnings for FDX and UPS"
        Function: get_next_earnings_from_identifiers(identifiers=["FDX", "UPS"])
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {
        Permission.EarningsPermission,
        Permission.TranscriptsPermission,
    }

    async def _arun(self, identifiers: list[str]) -> GetNextOrLatestEarningsFromIdentifiersResp:
        """"""
        earnings_responses = await get_earnings_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
        )
        output_model = GetNextOrLatestEarningsFromIdentifiersResp(results=dict(), errors=list())
        for identifier, earnings in earnings_responses.results.items():
            next_earnings = earnings.next_earnings
            if next_earnings:
                output_model.results[identifier] = next_earnings
            else:
                output_model.errors.append(f"No next earnings available for {identifier}.")
        # Add errors from the earnings fetch
        output_model.errors.extend(earnings_responses.errors)
        return output_model


async def get_earnings_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
) -> GetEarningsFromIdentifiersResp:
    """Fetch earnings for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_earnings_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                httpx_client=httpx_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, EarningsCallResp] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            results[task.result_key] = task.result

    return GetEarningsFromIdentifiersResp(results=results, errors=errors)


async def fetch_earnings_from_company_id(
    company_id: int,
    httpx_client: httpx.AsyncClient,
) -> EarningsCallResp:
    """Fetch earnings for one company_id."""
    url = f"/earnings/{company_id}"
    resp = await httpx_client.get(url=url)
    return EarningsCallResp.model_validate(resp.json())


async def get_transcript_from_key_dev_id(
    key_dev_id: int,
    httpx_client: httpx.AsyncClient,
) -> str:
    """Fetch raw transcript text for a key_dev_id."""
    url = f"/transcript/{key_dev_id}"
    resp = await httpx_client.get(url=url)
    transcript_data = resp.json()

    # Convert transcript components to raw text format (same as sync version)
    transcript_parts = []
    for component in transcript_data.get("transcript", []):
        person_name = component.get("person_name", "")
        text = component.get("text", "")
        transcript_parts.append(f"{person_name}: {text}")

    return "\n\n".join(transcript_parts)
