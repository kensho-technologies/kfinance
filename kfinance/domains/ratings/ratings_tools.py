from datetime import date
from textwrap import dedent
from typing import Type

import httpx
from pydantic import BaseModel, Field

from kfinance.client.permission_models import Permission
from kfinance.domains.ratings.id_resolution import resolve_entities
from kfinance.domains.ratings.ratings_models import IssuerRatingsResp
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithIdInfoAndErrors,
)


class GetIssuerRatingsFromIdentifierArgs(ToolArgsWithIdentifiers):
    pass


class GetIssuerRatingsFromIdentifiersResp(ToolRespWithIdInfoAndErrors[IssuerRatingsResp]):
    pass


class GetIssuerRatingsFromIdentifiers(KfinanceTool):
    name: str = "get_issuer_ratings_from_identifiers"
    description: str = dedent("""
        Get issuer-level ratings for a one or more identifiers.

        [ TODO: add more info ]

        Examples: [ADD EXAMPLES]
        Query: [ADD]
        Function: get_issuer_ratings_from_identifiers(identifiers=["AAPL", "USA"])
    """).strip()
    args_schema: Type[BaseModel] = GetIssuerRatingsFromIdentifierArgs
    accepted_permissions: set[Permission] | None = {Permission.RatingsPermission}

    async def _arun(
        self,
        identifiers: list[str],
    ) -> GetIssuerRatingsFromIdentifiersResp:
        """"""
        return await get_issuer_ratings_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
        )

async def get_issuer_ratings_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
) -> GetIssuerRatingsFromIdentifiersResp:
    """Fetch issuer ratings for a list of identifiers."""

    entity_resp = await resolve_entities(
        identifiers=[identifiers], httpx_client=httpx_client
    )
    errors: list[str] = list(entity_resp.errors.values())

    # check if identifiers were resolved
    if not entity_resp.identifiers_resolved:
        return GetIssuerRatingsFromIdentifiersResp(
            identifier_results={},
            identifier_info={},
            errors=errors,
        )
    
    entity_ids = [identifier.entitiy_id for identifier in entity_resp.identifiers_resolved]

    result = await fetch_issuer_ratings_from_identifiers(
        entity_ids=entity_ids,
        httpx_client=httpx_client,
    )

    identifier_results = {}
    if result.errors:
        errors.append(f"No results found for identifier {key}" for key in result.errors.keys())
    else:
        for key in result.keys():
            identifier_results[key] = result[key] 

    return GetIssuerRatingsFromIdentifiersResp(
        identifier_results=identifier_results,
        identifier_info=entity_resp.identifiers_resolved,
        errors=errors,
    )

async def fetch_issuer_ratings_from_identifiers(
    entity_ids: list[int],
    httpx_client: httpx.AsyncClient,
) -> IssuerRatingsResp:
    """Fetch issuer-level ratings for one or more entities."""

    # add optional fields if provided
    url = "/ratings/issuer_ratings/"
    payload: dict[str, list[str | int]] = {
        "entity_ids": entity_ids
    }

    resp = await httpx_client.post(url=url, json=payload)
    resp.raise_for_status()
    return IssuerRatingsResp.model_validate(resp.json())