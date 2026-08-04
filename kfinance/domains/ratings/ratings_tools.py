from textwrap import dedent
from typing import Type

import httpx
from pydantic import BaseModel

from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.models.dataset_filter_models import DatasetFilter
from kfinance.client.permission_models import Permission
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


class GetIssuerRatingsFromIdentifiersArgs(ToolArgsWithIdentifiers):
    pass


class GetIssuerRatingsFromIdentifiersResp(ToolRespWithErrors):
    """Response for issuer ratings using EntityInfo instead of IdentificationTripleWithCompanyInfo."""

    results: dict[str, EntityInfoWithResult]

    @classmethod
    def create(
        cls,
        identifier_results: dict[str, IssuerRatings],
        identifier_info: dict[str, EntityInfo],
        errors: list[str],
    ) -> "GetIssuerRatingsFromIdentifiersResp":
        """Factory method to create response by combining ratings with entity info."""
        combined_results: dict[str, EntityInfoWithResult] = {}

        for identifier, result in identifier_results.items():
            entity_info = identifier_info[identifier]

            combined_results[identifier] = EntityInfoWithResult(
                data=result,
                entity_name=entity_info.entity_name,
                ticker=entity_info.ticker,
                country=entity_info.country,
            )

        return cls(results=combined_results, errors=errors)


class GetIssuerRatingsFromIdentifiers(KfinanceTool):
    name: str = "get_issuer_ratings_from_identifiers"
    description: str = dedent("""
        Get issuer-level credit ratings for one or more entities (companies and sovereigns).

        Returns ratings from credit rating agencies organized by organization type (e.g., ICR) and rating type
        (e.g., FCLONG for foreign currency long-term, STDSHORT for short-term). Each rating includes the current
        rating, rating action, credit watch status, outlook, and historical ratings.

        - Supports multiple identifiers in a single call (tickers, company IDs, company names, country names, ISO alpha-3 codes, ISINs, CUSIPs).
        - Works with both corporate entities (e.g., "AAPL", "Microsoft") and sovereign entities (e.g., "USA", "Germany").
        - Returns the latest rating along with full rating history for each entity.
        - Includes outlook (Stable, Positive, Negative) and credit watch information when available.

        Examples:
        Query: "What are the credit ratings for Apple?"
        Function: get_issuer_ratings_from_identifiers(identifiers=["Apple"])

        Query: "Get issuer ratings for Microsoft and Amazon"
        Function: get_issuer_ratings_from_identifiers(identifiers=["Microsoft", "Amazon"])

        Query: "What is the sovereign credit rating for the United States?"
        Function: get_issuer_ratings_from_identifiers(identifiers=["United States"])

        Query: "Compare ratings for JPMorgan Chase and Bank of America"
        Function: get_issuer_ratings_from_identifiers(identifiers=["JPMorgan Chase", "Bank of America"])
    """).strip()
    args_schema: Type[BaseModel] = GetIssuerRatingsFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.OnlyStaffPermission}

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
    """Fetch issuer ratings for a list of identifiers.

    Uses /ids with datasets_filter=[RATINGS] and include_countries=True to resolve
    both company and sovereign identifiers.
    """
    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers,
        httpx_client=httpx_client,
        datasets_filter=[DatasetFilter.RATINGS],
        include_countries=True,
    )

    errors: list[str] = list(id_triple_resp.errors.values())

    # Check if any identifiers were resolved
    if not id_triple_resp.identifiers_to_id_triples:
        return GetIssuerRatingsFromIdentifiersResp.create(
            identifier_results={},
            identifier_info={},
            errors=errors,
        )

    # Build EntityInfo from resolved id triples (entity_id == company_id for ratings)
    identifier_info: dict[str, EntityInfo] = {}
    entity_ids: list[int] = []
    for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items():
        entity_info = EntityInfo(
            entity_id=id_triple.company_id,
            entity_name=id_triple.company_name,
            ticker=id_triple.ticker,
            country=id_triple.country,
        )
        identifier_info[identifier] = entity_info
        entity_ids.append(id_triple.company_id)

    result = await fetch_issuer_ratings_from_identifiers(
        entity_ids=entity_ids,
        httpx_client=httpx_client,
    )

    # Map results back from entity_id to original identifier
    entity_id_to_identifier = {
        info.entity_id: identifier for identifier, info in identifier_info.items()
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

    return GetIssuerRatingsFromIdentifiersResp.create(
        identifier_results=identifier_results,
        identifier_info=identifier_info,
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
