from textwrap import dedent
from typing import Type

import httpx
from pydantic import BaseModel

from pydantic import BaseModel, Field, computed_field

from kfinance.client.permission_models import Permission
from kfinance.domains.ratings.id_resolution import resolve_entities
from kfinance.domains.ratings.ratings_models import (
    EntityInfo,
    EntityInfoWithResult,
    IssuerRatings,
    IssuerRatingsResp,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
)


class GetIssuerRatingsFromIdentifierArgs(ToolArgsWithIdentifiers):
    pass


class GetIssuerRatingsFromIdentifiersResp(ToolRespWithErrors):
    """Response for issuer ratings using EntityInfo instead of IdentificationTripleWithCompanyInfo."""

    identifier_results: dict[str, IssuerRatings] = Field(exclude=True)
    identifier_info: dict[str, EntityInfo] = Field(exclude=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def results(self) -> dict[str, EntityInfoWithResult[IssuerRatings]]:
        """Combine ratings results with entity info."""
        output: dict[str, EntityInfoWithResult[IssuerRatings]] = {}

        for identifier, result in self.identifier_results.items():
            entity_info = self.identifier_info[identifier]

            output[identifier] = EntityInfoWithResult(
                data=result,
                entity_name=entity_info.entity_name,
                ticker=entity_info.ticker,
                country=entity_info.country,
            )

        return output


class GetIssuerRatingsFromIdentifiers(KfinanceTool):
    name: str = "get_issuer_ratings_from_identifiers"
    description: str = dedent("""
        Get issuer-level credit ratings for one or more entities (companies, sovereigns, municipalities, etc.).

        Returns ratings from credit rating agencies organized by organization type (e.g., ICR) and rating type
        (e.g., FCLONG for foreign currency long-term, STDSHORT for short-term). Each rating includes the current
        rating, rating action, credit watch status, outlook, and historical ratings.

        - Supports multiple identifiers in a single call (tickers, company names, country codes, ISINs, CUSIPs).
        - Works with both corporate entities (e.g., "AAPL", "Microsoft") and sovereign entities (e.g., "USA", "Germany").
        - Returns the latest rating along with full rating history for each entity.
        - Includes outlook (Stable, Positive, Negative) and credit watch information when available.

        Examples:
        Query: "What are the credit ratings for Apple?"
        Function: get_issuer_ratings_from_identifiers(identifiers=["AAPL"])

        Query: "Get issuer ratings for Microsoft and Amazon"
        Function: get_issuer_ratings_from_identifiers(identifiers=["MSFT", "AMZN"])

        Query: "What is the sovereign credit rating for the United States?"
        Function: get_issuer_ratings_from_identifiers(identifiers=["USA"])

        Query: "Compare ratings for JPMorgan Chase and Bank of America"
        Function: get_issuer_ratings_from_identifiers(identifiers=["JPM", "BAC"])
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

    entity_resp = await resolve_entities(identifiers=identifiers, httpx_client=httpx_client)
    errors: list[str] = [
        f"{identifier}: {error}" for identifier, error in entity_resp.errors.items()
    ]

    # check if identifiers were resolved
    if not entity_resp.identifiers_resolved:
        return GetIssuerRatingsFromIdentifiersResp(
            identifier_results={},
            identifier_info={},
            errors=errors,
        )

    entity_ids = [entity_info.entity_id for entity_info in entity_resp.identifiers_resolved.values()]

    result = await fetch_issuer_ratings_from_identifiers(
        entity_ids=entity_ids,
        httpx_client=httpx_client,
    )

    # Map results back from entity_id to original identifier
    # Reverse lookup: entity_id -> og identifier
    entity_id_to_identifier = {
        entity_info.entity_id: identifier
        for identifier, entity_info in entity_resp.identifiers_resolved.items()
    }

    identifier_results = {}
    for entity_id_str, ratings_data in result.results.items():
        entity_id = int(entity_id_str)
        original_identifier = entity_id_to_identifier[entity_id]
        identifier_results[original_identifier] = ratings_data

    # Add errors from API, mapping entity_id back to identifier
    for entity_id_str, error in result.errors.items():
        entity_id = int(entity_id_str)
        original_identifier = entity_id_to_identifier.get(entity_id, entity_id_str)
        errors.append(f"{original_identifier}: {error}")

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
    url = "/ratings/issuer_ratings/"
    payload: dict[str, str | list[int]] = {"entity_ids": entity_ids}

    resp = await httpx_client.post(url=url, json=payload)
    resp.raise_for_status()
    return IssuerRatingsResp.model_validate(resp.json())
