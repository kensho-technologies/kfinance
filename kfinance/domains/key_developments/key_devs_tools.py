from datetime import date
from textwrap import dedent
from typing import Type

import httpx
from pydantic import BaseModel, Field

from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.key_developments.key_devs_models import KeyDevCategoryType, KeyDevsResp
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifier,
    ToolRespWithIdInfoAndErrors,
)


class GetKeyDevsFromIdentifierArgs(ToolArgsWithIdentifier):
    start_date: date | None = Field(
        default=None,
        description="The start date for fetching key developments (inclusive). Use null to get all key developments from the beginning.",
    )
    end_date: date | None = Field(
        default=None,
        description="The end date for fetching key developments (inclusive). Use null to get all key developments up to the present.",
    )
    # no description because the description for enum fields comes from the enum docstring.
    key_dev_category: KeyDevCategoryType | None = Field(
        default=None,
    )


class GetKeyDevsFromIdentifierResp(ToolRespWithIdInfoAndErrors[KeyDevsResp]):
    pass


class GetKeyDevsFromIdentifier(KfinanceTool):
    name: str = "get_key_devs_from_identifier"
    description: str = dedent("""
        Get key development events for a single identifier within an optional date range.

        Key developments include events like client announcements, earnings releases, mergers and acquisitions,
        management changes, and other significant corporate events. Results are grouped by category.

        - Only one identifier can be queried at a time.
        - start_date and end_date are optional. Leave null to get all key developments.
        - Optionally filter by key_dev_category to get only specific types of events.
        - Results are categorized by event type (e.g., "Client Announcements", "Earnings Releases").
        - Each event includes a key_dev_id, situation description, dates, source, and company role.

        Examples:
        Query: "What are all the key developments for Apple?"
        Function: get_key_devs_from_identifier(identifier="Apple", start_date=null, end_date=null)

        Query: "What key developments happened at S&P Global between October and November 2025?"
        Function: get_key_devs_from_identifier(identifier="S&P Global", start_date="2025-10-01", end_date="2025-11-30")

        Query: "Get transaction-related key developments for Apple in 2025"
        Function: get_key_devs_from_identifier(identifier="Apple", start_date="2025-01-01", end_date="2025-12-31", key_dev_category=2)
    """).strip()
    args_schema: Type[BaseModel] = GetKeyDevsFromIdentifierArgs
    accepted_permissions: set[Permission] | None = {Permission.EarningsPermission}

    async def _arun(
        self,
        identifier: str,
        start_date: date | None = None,
        end_date: date | None = None,
        key_dev_category: KeyDevCategoryType | None = None,
    ) -> GetKeyDevsFromIdentifierResp:
        """"""
        return await get_key_devs_from_identifier(
            identifier=identifier,
            httpx_client=self.kfinance_client.httpx_client,
            start_date=start_date,
            end_date=end_date,
            key_dev_category=key_dev_category,
        )


async def get_key_devs_from_identifier(
    identifier: str,
    httpx_client: httpx.AsyncClient,
    start_date: date | None = None,
    end_date: date | None = None,
    key_dev_category: KeyDevCategoryType | None = None,
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
    httpx_client: httpx.AsyncClient,
    start_date: date | None = None,
    end_date: date | None = None,
    key_dev_category: KeyDevCategoryType | None = None,
) -> KeyDevsResp:
    """Fetch key developments for one company_id."""
    url = "/key_devs"
    payload: dict[str, str | int] = {
        "company_id": company_id,
    }

    # add optional fields if provided
    if start_date is not None:
        payload["start_date"] = start_date.isoformat()
    if end_date is not None:
        payload["end_date"] = end_date.isoformat()
    if key_dev_category is not None:
        payload["key_dev_category"] = key_dev_category.value

    resp = await httpx_client.post(url=url, json=payload)
    resp.raise_for_status()
    return KeyDevsResp.model_validate(resp.json())
