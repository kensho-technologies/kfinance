from collections import Counter
from textwrap import dedent
from typing import Type

import httpx
from pydantic import BaseModel, Field

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.corporate_tree.corporate_tree_models import (
    CorporateTreeNode,
    CorporateTreeResponse,
    CorporateTreeSearchResult,
    SearchMatch,
    SearchSummary,
    TreeRelationshipType,
    UltimateParentPathsResponse,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithIdInfoAndErrors,
)


class GetUltimateParentPathsFromIdentifiersResp(
    ToolRespWithIdInfoAndErrors[UltimateParentPathsResponse]
):
    pass


class GetUltimateParentPathsFromIdentifiers(KfinanceTool):
    name: str = "get_ultimate_parent_paths_from_identifiers"
    description: str = dedent("""
        Get the corporate ownership paths leading from each of the provided identifiers up to its ultimate parent companies.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - Each path is ordered from the queried company first to its ultimate parent last.
        - A company can be owned through more than one chain, so more than one path may be returned.
        - Each element's relationship_type describes how that element is owned by the next element in the path. The ultimate parent ending a path has a null parent_company_id and a null relationship_type.
        - A company with no controlling parent is its own ultimate parent, returned as a single path holding only that company.
        - Only current relationships are followed; prior/historical ownership is never included.

        Examples:
        Query: "Who is the ultimate parent of Instagram?"
        Function: get_ultimate_parent_paths_from_identifiers(identifiers=["Instagram"])

        Query: "Show the ownership chain for YouTube and WhatsApp"
        Function: get_ultimate_parent_paths_from_identifiers(identifiers=["YouTube", "WhatsApp"])
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    # TODO: Specify permissions
    accepted_permissions: set[Permission] | None = None

    async def _arun(self, identifiers: list[str]) -> GetUltimateParentPathsFromIdentifiersResp:
        """"""
        return await get_ultimate_parent_paths_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def get_ultimate_parent_paths_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
) -> GetUltimateParentPathsFromIdentifiersResp:
    """Fetch the ultimate parent paths for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_ultimate_parent_paths,
            kwargs=dict(
                company_id=id_triple.company_id,
                httpx_client=httpx_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, UltimateParentPathsResponse] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            results[task.result_key] = task.result

    return GetUltimateParentPathsFromIdentifiersResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
    )


async def fetch_ultimate_parent_paths(
    company_id: int,
    httpx_client: httpx.AsyncClient,
) -> UltimateParentPathsResponse:
    """Fetch every path from a single company up to its ultimate parents."""
    resp = await httpx_client.get(url=f"/corporate_tree/{company_id}/ultimate_parent_paths")
    resp.raise_for_status()
    return UltimateParentPathsResponse.model_validate(resp.json())


class SearchCorporateTreeFromIdentifiersArgs(ToolArgsWithIdentifiers):
    relationship_type: list[TreeRelationshipType] | None = Field(
        default=None,
        description="Filter by relationship type(s). Nodes matching ANY of the listed types are included.",
    )
    country_iso_code: list[str] | None = Field(
        default=None,
        description="Countries to filter by, as ISO 3166-1 alpha-3 codes only (e.g., ['USA', 'GBR', 'DEU']). Nodes in ANY of the listed countries are included.",
    )
    name_contains: list[str] | None = Field(
        default=None,
        description="Substring(s) to match against company names (case-insensitive). Nodes matching ANY of the listed substrings are included.",
    )
    max_depth: int | None = Field(
        default=None,
        description="How many levels below the company to search. Omit to search the entire tree. Use max_depth=1 to search direct relationships only.",
        ge=0,
    )
    include_prior: bool = Field(
        default=False,
        description="If true, include prior/historical relationships in the tree. By default only current relationships are included.",
    )
    limit: int = Field(
        default=50,
        description="Maximum number of matching nodes to return per identifier (1-200).",
        ge=1,
        le=200,
    )


class SearchCorporateTreeFromIdentifiersResp(
    ToolRespWithIdInfoAndErrors[CorporateTreeSearchResult]
):
    pass


class SearchCorporateTreeFromIdentifiers(KfinanceTool):
    name: str = "search_corporate_tree_from_identifiers"
    description: str = dedent("""
        Search the companies below a company in its corporate tree for entities matching the specified filters.

        Filters are combined with AND logic across filter types. When a filter contains multiple values, a node matches if it matches ANY value in the list (OR within a filter).

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - Returns up to `limit` matches per identifier (default 50) in `matches`. `summary.total_matches` reports how many matched in total. There is no pagination.
        - `queried_company` echoes the company whose tree was searched. It is the top of the searched tree, not necessarily an ultimate parent; use get_ultimate_parent_paths_from_identifiers to look upward from it.
        - The queried company itself is never a match; only the companies below it are searched.
        - Set max_depth to limit how deep to search. E.g. max_depth=1 searches direct children only. Omit it to search the whole tree.
        - When max_depth cuts the search short, `summary.search_was_depth_limited` is true and the `summary.companies_searched`/`relationships_searched`/`deepest_level_searched` counts describe only the searched portion, not the whole tree. To see deeper, call again with a larger max_depth or omit it entirely.
        - Set include_prior=true to also include historical relationships that are no longer active.
        - A company owned through several parents appears once per parent, each with its own parent_company_id. `summary.distinct_companies` counts the underlying companies.
        - country_iso_code takes ISO 3166-1 alpha-3 codes only. Convert country names to codes before calling, e.g. Germany -> DEU.

        Examples:
        Query: "What subsidiaries does Microsoft have in Germany?"
        Function: search_corporate_tree_from_identifiers(identifiers=["Microsoft"], country_iso_code=["DEU"], relationship_type=["subsidiary_or_operating_unit"])

        Query: "Find all entities named 'Capital' or 'Global' under JPMorgan"
        Function: search_corporate_tree_from_identifiers(identifiers=["JPM"], name_contains=["Capital", "Global"])

        Query: "List the direct subsidiaries of Apple"
        Function: search_corporate_tree_from_identifiers(identifiers=["Apple"], max_depth=1, relationship_type=["subsidiary_or_operating_unit"])

        Query: "Find all subsidiaries and investment arms of S&P Global in the US, UK, and India"
        Function: search_corporate_tree_from_identifiers(identifiers=["SPGI"], relationship_type=["subsidiary_or_operating_unit", "investment_arm"], country_iso_code=["USA", "GBR", "IND"])
    """).strip()
    args_schema: Type[BaseModel] = SearchCorporateTreeFromIdentifiersArgs
    # TODO: Specify permissions
    accepted_permissions: set[Permission] | None = None

    async def _arun(
        self,
        identifiers: list[str],
        relationship_type: list[TreeRelationshipType] | None = None,
        country_iso_code: list[str] | None = None,
        name_contains: list[str] | None = None,
        max_depth: int | None = None,
        include_prior: bool = False,
        limit: int = 50,
    ) -> SearchCorporateTreeFromIdentifiersResp:
        """"""
        return await search_corporate_tree_from_identifiers(
            identifiers=identifiers,
            relationship_type=relationship_type,
            country_iso_code=country_iso_code,
            name_contains=name_contains,
            max_depth=max_depth,
            include_prior=include_prior,
            limit=limit,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def search_corporate_tree_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
    relationship_type: list[TreeRelationshipType] | None = None,
    country_iso_code: list[str] | None = None,
    name_contains: list[str] | None = None,
    max_depth: int | None = None,
    include_prior: bool = False,
    limit: int = 50,
) -> SearchCorporateTreeFromIdentifiersResp:
    """Search corporate trees for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_and_search_corporate_tree,
            kwargs=dict(
                company_id=id_triple.company_id,
                httpx_client=httpx_client,
                relationship_type=relationship_type,
                country_iso_code=country_iso_code,
                name_contains=name_contains,
                max_depth=max_depth,
                include_prior=include_prior,
                limit=limit,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, CorporateTreeSearchResult] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            results[task.result_key] = task.result

    return SearchCorporateTreeFromIdentifiersResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
    )


def _node_matches(
    node: CorporateTreeNode,
    relationship_types: list[TreeRelationshipType] | None,
    country_iso_codes: list[str] | None,
    name_substrings: list[str] | None,
) -> bool:
    """Whether a node satisfies every supplied filter. Country and name matching is case-insensitive."""
    if relationship_types is not None and node.relationship_type not in relationship_types:
        return False

    if country_iso_codes is not None:
        iso_country = node.company.iso_country
        if iso_country is None:
            return False
        if not any(iso_country.casefold() == code.casefold() for code in country_iso_codes):
            return False

    if name_substrings is not None:
        node_name = node.company.company_name.casefold()
        if not any(substring.casefold() in node_name for substring in name_substrings):
            return False

    return True


async def fetch_and_search_corporate_tree(
    company_id: int,
    httpx_client: httpx.AsyncClient,
    relationship_type: list[TreeRelationshipType] | None = None,
    country_iso_code: list[str] | None = None,
    name_contains: list[str] | None = None,
    max_depth: int | None = None,
    include_prior: bool = False,
    limit: int = 50,
) -> CorporateTreeSearchResult:
    """Fetch the corporate tree for a single company and search it."""
    response = await fetch_corporate_tree(
        company_id=company_id,
        httpx_client=httpx_client,
        include_prior=include_prior,
        max_depth=max_depth,
    )

    # The API already applied max_depth, so there is no depth filtering left to do here.
    matches = [
        node
        for node in response.nodes
        if _node_matches(node, relationship_type, country_iso_code, name_contains)
    ]

    return CorporateTreeSearchResult(
        queried_company=response.root,
        matches=[
            SearchMatch(
                company_id=node.company.company_id,
                company_name=node.company.company_name,
                country=node.company.country,
                iso_country=node.company.iso_country,
                parent_company_id=node.parent_company_id,
                level=node.level,
                relationship_type=node.relationship_type,
                relationship_status=node.relationship_status,
            )
            for node in matches[:limit]
        ],
        summary=SearchSummary(
            total_matches=len(matches),
            distinct_companies=len({node.company.company_id for node in matches}),
            showing=min(len(matches), limit),
            matches_by_level={
                str(level): count
                for level, count in sorted(Counter(node.level for node in matches).items())
            },
            companies_searched=response.summary.total_companies,
            relationships_searched=response.summary.total_edges,
            deepest_level_searched=response.summary.max_depth,
            search_was_depth_limited=response.truncation is not None,
        ),
    )


async def fetch_corporate_tree(
    company_id: int,
    httpx_client: httpx.AsyncClient,
    include_prior: bool = False,
    max_depth: int | None = None,
) -> CorporateTreeResponse:
    """Fetch the corporate tree for a single company.

    max_depth=None traverses the whole tree.
    """
    url = f"/corporate_tree/{company_id}?include_prior={str(include_prior).lower()}"
    if max_depth is not None:
        url += f"&max_depth={max_depth}"
    resp = await httpx_client.get(url=url)
    resp.raise_for_status()
    return CorporateTreeResponse.model_validate(resp.json())
