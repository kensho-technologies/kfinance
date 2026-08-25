import json
from textwrap import dedent
from typing import Any, Type

import httpx
from pydantic import BaseModel, Field, field_validator

from kfinance.client.permission_models import Permission
from kfinance.domains.ratings.id_resolution import resolve_entities
from kfinance.domains.ratings.ratings_models import (
    EntityInfo,
    EntityInfoWithResult,
    IssuerRatings,
    IssuerRatingsResp,
    SecurityRatings,
    SecurityRatingsResp,
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


class GetSecurityRatingsFromIdentifiersArgs(BaseModel):
    security_identifiers: list[str] = Field(
        min_length=1,
        description="The security identifiers, which can be a list of ISINs, CUSIPs, CINS, or CIQ security_ids",
    )

    @field_validator("security_identifiers", mode="before")
    @classmethod
    def coerce_security_identifiers(cls, v: Any) -> list[str]:
        """Handle bare string or int and stringified JSON list.

        Coerces single values and JSON strings into list[str].
        """
        if isinstance(v, str):
            v = v.strip()
            # Handle stringified JSON lists like '["123", "456"]'
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item) for item in parsed]
                except (json.JSONDecodeError, ValueError):
                    pass
            # Bare string like "123456789" -> ["123456789"]
            return [v]
        # Handle bare int like 123456789 -> ["123456789"]
        if isinstance(v, int):
            return [str(v)]
        # Already a list
        return [str(item) for item in v]


class GetSecurityRatingsFromIdentifiersResp(ToolRespWithErrors):
    """Response for security ratings."""

    results: dict[str, SecurityRatings] = Field(default_factory=dict)


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


class GetSecurityRatingsFromIdentifiers(KfinanceTool):
    name: str = "get_security_ratings_from_identifiers"
    description: str = dedent("""
        Get credit ratings for one or more securities.

        Returns ratings from credit rating agencies organized by security identifier and rating type
        (e.g., FCLONG for foreign currency long-term, STDSHORT for short-term).

        - Supports multiple security identifiers in a single call (CIQ security IDs, ISINs, CUSIPs, CINSs).
        - Returns the latest rating along with full rating history for each security.
        - Includes outlook (Stable, Positive, Negative) and credit watch information when available.

        Examples:
        Query: "What are the credit ratings for security XXX?"
        Function: get_security_ratings_from_identifiers(security_identifiers=["XXX"])

        Query: "Get ratings for securities 1230 and XXX."
        Function: get_security_ratings_from_identifiers(security_identifiers=["1230", "XXX"])
    """).strip()
    args_schema: Type[BaseModel] = GetSecurityRatingsFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.OnlyStaffPermission}

    async def _arun(
        self,
        security_identifiers: list[str],
    ) -> GetSecurityRatingsFromIdentifiersResp:
        """"""
        return await get_security_ratings_from_identifiers(
            security_ids=security_identifiers,
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
        return GetIssuerRatingsFromIdentifiersResp.create(
            identifier_results={},
            identifier_info={},
            errors=errors,
        )

    entity_ids = [
        entity_info.entity_id for entity_info in entity_resp.identifiers_resolved.values()
    ]

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

    return GetIssuerRatingsFromIdentifiersResp.create(
        identifier_results=identifier_results,
        identifier_info=entity_resp.identifiers_resolved,
        errors=errors,
    )


async def get_security_ratings_from_identifiers(
    security_ids: list[str],
    httpx_client: httpx.AsyncClient,
) -> GetSecurityRatingsFromIdentifiersResp:
    """Fetch security ratings for a list of identifiers."""

    result = await fetch_security_ratings_from_identifiers(
        security_ids=security_ids,
        httpx_client=httpx_client,
    )

    # Results are already mapped from original identifier to ciq security id.
    errors = [f"{identifier}: {error}" for identifier, error in result.errors.items()]
    return GetSecurityRatingsFromIdentifiersResp(
        results=result.results,
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


async def fetch_security_ratings_from_identifiers(
    security_ids: list[str],
    httpx_client: httpx.AsyncClient,
) -> SecurityRatingsResp:
    """Fetch security-level ratings for one or more securities."""
    url = "/ratings/security_ratings/"
    payload: dict[str, str | list[str]] = {"security_ids": security_ids}

    resp = await httpx_client.post(url=url, json=payload)
    resp.raise_for_status()
    return SecurityRatingsResp.model_validate(resp.json())
