from datetime import date
from textwrap import dedent
from typing import Any, Type

import httpx2
from pydantic import BaseModel, Field, model_validator

from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.key_developments.key_devs_models import (
    KeyDevCategoryType,
    KeyDevEventType,
    KeyDevsResp,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifier,
    ToolRespWithIdInfoAndErrors,
)


class GetKeyDevsFromIdentifierArgs(ToolArgsWithIdentifier):
    @model_validator(mode="before")
    @classmethod
    def accept_identifiers_for_identifier_field(cls, data: Any) -> Any:
        """Accept 'identifiers' (plural) as an alias for 'identifier' (singular).

        Every other kfinance tool uses 'identifiers' (plural), so LLMs
        extrapolate that pattern to this tool.
        """
        if isinstance(data, dict) and "identifiers" in data and "identifier" not in data:
            ids = data.pop("identifiers")
            data["identifier"] = ids[0] if isinstance(ids, list) else ids
        return data

    start_date: date | None = Field(
        default=None,
        description="Earliest announced_date_utc (YYYY-MM-DD, inclusive). Events are announced weeks to months before they happen, so omit it to find a specific call.",
    )
    end_date: date | None = Field(
        default=None,
        description='Latest announced_date_utc (YYYY-MM-DD, inclusive). Set it when the question names an end, for example "in 2024 and 2025" is 2025-12-31. Use null for no upper bound.',
    )
    key_dev_category: KeyDevCategoryType | None = Field(
        default=None,
    )
    event_type: KeyDevEventType | None = Field(
        default=None,
    )
    transcripts_only: bool | None = Field(
        default=None,
        description="True returns only events that have a transcript (earnings calls included).",
    )


class GetKeyDevsFromIdentifierResp(ToolRespWithIdInfoAndErrors[KeyDevsResp]):
    pass


class GetKeyDevsFromIdentifier(KfinanceTool):
    name: str = "get_key_devs_from_identifier"
    description: str = dedent("""
        Get key development events (announcements, filings, calls, presentations) for one identifier, grouped by event type. Each event has key_dev_id, situation, announced_date_utc, most_important_date_utc (the event's own date) and has_transcript.

        - Earnings calls: use get_earnings_from_identifiers. This tool covers all other events.
        - To find a specific call, omit start_date, match on most_important_date_utc, and pass its key_dev_id to get_transcript_from_key_dev_id.
        - Long results are cut to the most recent events and next_time_band is set. Page back only if the question needs earlier events.

        Examples:
        Query: "What are all the key developments for Apple?"
        Function: get_key_devs_from_identifier(identifier="Apple")

        Query: "What key developments happened at S&P Global between October and November 2025?"
        Function: get_key_devs_from_identifier(identifier="S&P Global", start_date="2025-10-01", end_date="2025-11-30")

        Query: "Get transaction-related key developments for Cisco in 2025"
        Function: get_key_devs_from_identifier(identifier="Cisco", start_date="2025-01-01", end_date="2025-12-31", key_dev_category="announced_or_completed_transactions")

        Query: "Show what Walgreens said when it updated its outlook in December 2021"
        Function 1: get_key_devs_from_identifier(identifier="Walgreens", event_type="guidance_update_call", transcripts_only=True)
        Function 2: get_transcript_from_key_dev_id(key_dev_id=<key_dev_id>)
    """).strip()
    args_schema: Type[BaseModel] = GetKeyDevsFromIdentifierArgs
    accepted_permissions: set[Permission] | None = {Permission.EarningsPermission}

    async def _arun(
        self,
        identifier: str,
        start_date: date | None = None,
        end_date: date | None = None,
        key_dev_category: KeyDevCategoryType | None = None,
        event_type: KeyDevEventType | None = None,
        transcripts_only: bool | None = None,
    ) -> GetKeyDevsFromIdentifierResp:
        """"""
        return await get_key_devs_from_identifier(
            identifier=identifier,
            httpx_client=self.kfinance_client.httpx_client,
            start_date=start_date,
            end_date=end_date,
            key_dev_category=key_dev_category,
            event_type=event_type,
            transcripts_only=transcripts_only,
        )


async def get_key_devs_from_identifier(
    identifier: str,
    httpx_client: httpx2.AsyncClient,
    start_date: date | None = None,
    end_date: date | None = None,
    key_dev_category: KeyDevCategoryType | None = None,
    event_type: KeyDevEventType | None = None,
    transcripts_only: bool | None = None,
) -> GetKeyDevsFromIdentifierResp:
    """Fetch key developments for a single identifier."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=[identifier], httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    # check if identifier was resolved
    if identifier not in id_triple_resp.identifiers_to_id_triples:
        return GetKeyDevsFromIdentifierResp(
            identifier_results={},
            identifier_info={},
            errors=errors,
        )

    id_triple = id_triple_resp.identifiers_to_id_triples[identifier]

    result = await fetch_key_devs_from_company_id(
        company_id=id_triple.company_id,
        httpx_client=httpx_client,
        start_date=start_date,
        end_date=end_date,
        key_dev_category=key_dev_category,
        event_type=event_type,
        transcripts_only=transcripts_only,
    )

    identifier_results = {}
    if result.errors:
        errors.append(f"No result found for {identifier}")
    else:
        identifier_results[identifier] = result

    return GetKeyDevsFromIdentifierResp(
        identifier_results=identifier_results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
    )


async def fetch_key_devs_from_company_id(
    company_id: int,
    httpx_client: httpx2.AsyncClient,
    start_date: date | None = None,
    end_date: date | None = None,
    key_dev_category: KeyDevCategoryType | None = None,
    event_type: KeyDevEventType | None = None,
    transcripts_only: bool | None = None,
) -> KeyDevsResp:
    """Fetch key developments for one company_id."""
    url = "/key_devs/"
    payload: dict[str, str | int | bool] = {
        "company_id": company_id,
    }

    # add optional fields if provided
    if start_date is not None:
        payload["start_date"] = start_date.isoformat()
    if end_date is not None:
        payload["end_date"] = end_date.isoformat()
    if key_dev_category is not None:
        payload["key_dev_category"] = key_dev_category.value
    if event_type is not None:
        payload["event_type"] = event_type.value
    if transcripts_only:
        payload["transcripts_only"] = True

    resp = await httpx_client.post(url=url, json=payload)
    resp.raise_for_status()
    return KeyDevsResp.model_validate(resp.json())
