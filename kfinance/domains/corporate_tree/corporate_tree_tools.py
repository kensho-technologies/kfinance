from textwrap import dedent
from typing import Type

import httpx
from pydantic import BaseModel, Field

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.kfinance import CorporateTree, CorporateTreeNode
from kfinance.client.permission_models import Permission
from kfinance.domains.corporate_tree.corporate_tree_models import (
    CompanyInfo,
    CorporateTreeResponse,
    TreeNode,
    TreeRelationshipType,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithIdInfoAndErrors,
)


# --- Shared helpers ---


def build_corporate_tree_from_response(
    response: CorporateTreeResponse,
    kfinance_api_client: object,
) -> CorporateTree:
    """Build a CorporateTree from an API response (reuses client classes)."""

    def _build_node(tree_node: TreeNode) -> CorporateTreeNode:
        return CorporateTreeNode(
            kfinance_api_client=kfinance_api_client,
            company_info=tree_node.company,
            relationship_type=tree_node.relationship_type,
            relationship_status=tree_node.relationship_status,
            controlling_interest=tree_node.controlling_interest,
            children=[_build_node(child) for child in tree_node.children],
        )

    root_node = CorporateTreeNode(
        kfinance_api_client=kfinance_api_client,
        company_info=response.root.company,
        relationship_type=None,
        relationship_status=None,
        controlling_interest=None,
        children=[_build_node(child) for child in response.root.children],
    )

    return CorporateTree(
        kfinance_api_client=kfinance_api_client,
        root_node=root_node,
        ultimate_parent_path=response.ultimate_parent_path,
        truncation=response.truncation,
    )


async def fetch_corporate_tree(
    company_id: int,
    httpx_client: httpx.AsyncClient,
    include_prior: bool = False,
    include_ultimate_parent_path: bool = False,
    max_depth: int = 20,
) -> CorporateTreeResponse:
    """Fetch the corporate tree for a single company."""
    url = (
        f"/corporate_tree/{company_id}"
        f"?include_prior={str(include_prior).lower()}"
        f"&include_ultimate_parent_path={str(include_ultimate_parent_path).lower()}"
        f"&max_depth={max_depth}"
    )
    resp = await httpx_client.get(url=url)
    resp.raise_for_status()
    return CorporateTreeResponse.model_validate(resp.json())


# --- Response models ---


class UltimateParentPathResult(BaseModel):
    """Path from ultimate parent down to the queried company."""

    path: list[CompanyInfo]


class SearchNodeResult(BaseModel):
    """A single node returned from a corporate tree search."""

    company_id: int
    company_name: str
    country: str | None = None
    iso_country: str | None = None
    relationship_type: str
    relationship_status: str
    controlling_interest: bool
    level: int = Field(description="Depth in the tree (0 = root, 1 = direct child, etc.)")


class SearchSummary(BaseModel):
    """Summary metadata about the search results."""

    total_matches: int
    showing: int
    matches_by_level: dict[str, int]
    tree_nodes_searched: int
    tree_truncated: bool


class CorporateTreeSearchResult(BaseModel):
    """Search results from the corporate tree."""

    nodes: list[SearchNodeResult]
    summary: SearchSummary


class SummaryCompanyInfo(BaseModel):
    """Minimal company info for summary results."""

    id: int
    name: str


class SummaryCountryInfo(BaseModel):
    """Country entry in the top_countries list."""

    country: str
    iso_country: str
    count: int


class SummaryChildInfo(BaseModel):
    """A direct child with its descendant count."""

    id: int
    name: str
    descendants: int


class CorporateTreeSummaryResult(BaseModel):
    """Summary statistics for a corporate tree."""

    tree_size: int
    tree_truncated: bool
    direct_children: int
    depth: int
    ultimate_parent: SummaryCompanyInfo | None
    by_type: dict[str, int]
    top_countries: list[SummaryCountryInfo]
    other_countries_count: int
    largest_children: list[SummaryChildInfo]


# --- Tool 1: Get Ultimate Parent Path ---


class GetUltimateParentPathFromIdentifiersResp(ToolRespWithIdInfoAndErrors[UltimateParentPathResult]):
    pass


class GetUltimateParentPathFromIdentifiers(KfinanceTool):
    name: str = "get_ultimate_parent_path_from_identifiers"
    description: str = dedent("""
        Get the corporate ownership path from the ultimate parent company down to each of the provided identifiers.

        Returns the chain of parent companies from the top-level ultimate parent to the queried company.
        Useful for determining "who ultimately owns this company?" or understanding the corporate hierarchy.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - The path is ordered from ultimate parent (first) to the queried company (last).
        - If the company is itself the ultimate parent, the path contains only that company.

        Examples:
        Query: "Who is the ultimate parent of Instagram?"
        Function: get_ultimate_parent_path_from_identifiers(identifiers=["Instagram"])

        Query: "Show the ownership chain for YouTube and WhatsApp"
        Function: get_ultimate_parent_path_from_identifiers(identifiers=["YouTube", "WhatsApp"])
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = None

    async def _arun(self, identifiers: list[str]) -> GetUltimateParentPathFromIdentifiersResp:
        """"""
        return await get_ultimate_parent_path_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def get_ultimate_parent_path_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
) -> GetUltimateParentPathFromIdentifiersResp:
    """Fetch the ultimate parent path for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_ultimate_parent_path,
            kwargs=dict(
                company_id=id_triple.company_id,
                httpx_client=httpx_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, UltimateParentPathResult] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            results[task.result_key] = task.result

    return GetUltimateParentPathFromIdentifiersResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
    )


async def fetch_ultimate_parent_path(
    company_id: int,
    httpx_client: httpx.AsyncClient,
) -> UltimateParentPathResult:
    """Fetch the ultimate parent path for a single company."""
    # max_depth=0: we only need the path, not the full tree
    response = await fetch_corporate_tree(
        company_id=company_id,
        httpx_client=httpx_client,
        include_ultimate_parent_path=True,
        max_depth=0,
    )

    if response.ultimate_parent_path is not None:
        path = response.ultimate_parent_path
    else:
        # Company is its own ultimate parent
        path = [response.root.company]

    return UltimateParentPathResult(path=path)


# --- Tool 2: Search Corporate Tree ---


class SearchCorporateTreeArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    relationship_type: TreeRelationshipType | None = Field(
        default=None,
    )
    country: str | None = Field(
        default=None,
        description="ISO country code to filter by (e.g., 'USA', 'GBR')",
    )
    name: str | None = Field(
        default=None,
        description="Substring to match against company names (case-insensitive)",
    )
    direct_children_only: bool = Field(
        default=False,
        description="If true, only search direct subsidiaries. If false, search the entire tree.",
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


class SearchCorporateTreeFromIdentifiersResp(ToolRespWithIdInfoAndErrors[CorporateTreeSearchResult]):
    pass


class SearchCorporateTreeFromIdentifiers(KfinanceTool):
    name: str = "search_corporate_tree_from_identifiers"
    description: str = dedent("""
        Search a company's corporate tree for subsidiaries, affiliates, or other related entities matching the specified filters.

        Filters are combined with AND logic. At least one filter (relationship_type, country, or name) should be provided for useful results.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - Returns up to `limit` matching nodes per identifier (default 50, max 200).
        - Set direct_children_only=true to limit results to immediate subsidiaries only.
        - Set include_prior=true to include historical/prior relationships that are no longer active.

        Examples:
        Query: "What subsidiaries does Microsoft have in Germany?"
        Function: search_corporate_tree_from_identifiers(identifiers=["Microsoft"], country="DEU", relationship_type="SUBSIDIARY_OR_OPERATING_UNIT")

        Query: "Find all entities named 'Capital' under JPMorgan"
        Function: search_corporate_tree_from_identifiers(identifiers=["JPM"], name="Capital")

        Query: "List the direct subsidiaries of Apple"
        Function: search_corporate_tree_from_identifiers(identifiers=["Apple"], direct_children_only=true, relationship_type="SUBSIDIARY_OR_OPERATING_UNIT")
    """).strip()
    args_schema: Type[BaseModel] = SearchCorporateTreeArgs
    accepted_permissions: set[Permission] | None = None

    async def _arun(
        self,
        identifiers: list[str],
        relationship_type: TreeRelationshipType | None = None,
        country: str | None = None,
        name: str | None = None,
        direct_children_only: bool = False,
        include_prior: bool = False,
        limit: int = 50,
    ) -> SearchCorporateTreeFromIdentifiersResp:
        """"""
        return await search_corporate_tree_from_identifiers(
            identifiers=identifiers,
            relationship_type=relationship_type,
            country=country,
            name=name,
            direct_children_only=direct_children_only,
            include_prior=include_prior,
            limit=limit,
            httpx_client=self.kfinance_client.httpx_client,
            kfinance_api_client=self.kfinance_client.kfinance_api_client,
        )


async def search_corporate_tree_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
    kfinance_api_client: object,
    relationship_type: TreeRelationshipType | None = None,
    country: str | None = None,
    name: str | None = None,
    direct_children_only: bool = False,
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
                kfinance_api_client=kfinance_api_client,
                relationship_type=relationship_type,
                country=country,
                name=name,
                direct_children_only=direct_children_only,
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


async def fetch_and_search_corporate_tree(
    company_id: int,
    httpx_client: httpx.AsyncClient,
    kfinance_api_client: object,
    relationship_type: TreeRelationshipType | None = None,
    country: str | None = None,
    name: str | None = None,
    direct_children_only: bool = False,
    include_prior: bool = False,
    limit: int = 50,
) -> CorporateTreeSearchResult:
    """Fetch the corporate tree and search it for a single company."""
    response = await fetch_corporate_tree(
        company_id=company_id,
        httpx_client=httpx_client,
        include_prior=include_prior,
        max_depth=1 if direct_children_only else 20,
    )

    tree = build_corporate_tree_from_response(response, kfinance_api_client)

    # Build a depth map (node object id → level) via traversal, and count total nodes
    depth_map: dict[int, int] = {}
    tree_nodes_searched = 0

    def _map_depths(node: CorporateTreeNode, level: int) -> None:
        nonlocal tree_nodes_searched
        tree_nodes_searched += 1
        depth_map[id(node)] = level
        for child in node.children:
            _map_depths(child, level + 1)

    _map_depths(tree.root, 0)

    # Search without limit to get total matches and level breakdown
    all_matching_nodes = tree.search(
        relationship_type=relationship_type,
        country=country,
        name=name,
        limit=None,
        max_depth=1 if direct_children_only else None,
    )

    # Compute matches_by_level across all matches
    matches_by_level: dict[str, int] = {}
    for node in all_matching_nodes:
        level_key = str(depth_map[id(node)])
        matches_by_level[level_key] = matches_by_level.get(level_key, 0) + 1

    # Truncate to limit for the returned nodes
    returned_nodes = all_matching_nodes[:limit]

    nodes = [
        SearchNodeResult(
            company_id=node.company_id,
            company_name=node.company_name,
            country=node.country,
            iso_country=node.iso_country,
            relationship_type=node.relationship_type.value if node.relationship_type else "",
            relationship_status=node.relationship_status.value if node.relationship_status else "",
            controlling_interest=node.controlling_interest or False,
            level=depth_map[id(node)],
        )
        for node in returned_nodes
    ]

    return CorporateTreeSearchResult(
        nodes=nodes,
        summary=SearchSummary(
            total_matches=len(all_matching_nodes),
            showing=len(nodes),
            matches_by_level=matches_by_level,
            tree_nodes_searched=tree_nodes_searched,
            tree_truncated=tree.is_truncated,
        ),
    )


# --- Tool 3: Get Corporate Tree Summary ---


class GetCorporateTreeSummaryFromIdentifiersResp(
    ToolRespWithIdInfoAndErrors[CorporateTreeSummaryResult]
):
    pass


class GetCorporateTreeSummaryFromIdentifiers(KfinanceTool):
    name: str = "get_corporate_tree_summary_from_identifiers"
    description: str = dedent("""
        Get summary statistics about a company's corporate tree structure.

        Returns aggregate information including total number of entities, breakdown by corporate level,
        by relationship type (subsidiary, affiliate, investment arm, merged entity), and by country.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - Also reports whether the tree was truncated due to size limits.

        Examples:
        Query: "How many subsidiaries does Berkshire Hathaway have?"
        Function: get_corporate_tree_summary_from_identifiers(identifiers=["Berkshire Hathaway"])

        Query: "Compare the corporate tree sizes of Apple and Microsoft"
        Function: get_corporate_tree_summary_from_identifiers(identifiers=["Apple", "Microsoft"])
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = None

    async def _arun(self, identifiers: list[str]) -> GetCorporateTreeSummaryFromIdentifiersResp:
        """"""
        return await get_corporate_tree_summary_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
            kfinance_api_client=self.kfinance_client.kfinance_api_client,
        )


async def get_corporate_tree_summary_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
    kfinance_api_client: object,
) -> GetCorporateTreeSummaryFromIdentifiersResp:
    """Fetch corporate tree summaries for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_and_summarize_corporate_tree,
            kwargs=dict(
                company_id=id_triple.company_id,
                httpx_client=httpx_client,
                kfinance_api_client=kfinance_api_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, CorporateTreeSummaryResult] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            results[task.result_key] = task.result

    return GetCorporateTreeSummaryFromIdentifiersResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
    )


async def fetch_and_summarize_corporate_tree(
    company_id: int,
    httpx_client: httpx.AsyncClient,
    kfinance_api_client: object,
) -> CorporateTreeSummaryResult:
    """Fetch the corporate tree and compute summary for a single company."""
    response = await fetch_corporate_tree(
        company_id=company_id,
        httpx_client=httpx_client,
        include_ultimate_parent_path=True,
        max_depth=20,
    )

    tree = build_corporate_tree_from_response(response, kfinance_api_client)

    # Count descendants for each node via post-order traversal
    def _count_descendants(node: CorporateTreeNode) -> int:
        count = 0
        for child in node.children:
            count += 1 + _count_descendants(child)
        return count

    # Compute tree depth (max level)
    def _max_depth(node: CorporateTreeNode, level: int) -> int:
        if not node.children:
            return level
        return max(_max_depth(child, level + 1) for child in node.children)

    # Compute by_type and country counts via full traversal
    by_type: dict[str, int] = {}
    country_counts: dict[str, tuple[str, int]] = {}  # iso_country -> (full_name, count)

    def _traverse(node: CorporateTreeNode) -> None:
        if node.relationship_type is not None:
            type_key = node.relationship_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

        iso = node.iso_country or "Unknown"
        if iso in country_counts:
            full_name, count = country_counts[iso]
            country_counts[iso] = (full_name, count + 1)
        else:
            country_counts[iso] = (node.country or "Unknown", 1)

        for child in node.children:
            _traverse(child)

    _traverse(tree.root)

    # Tree size includes root
    tree_size = 1 + sum(by_type.values())

    # Top 5 countries by count
    sorted_countries = sorted(country_counts.items(), key=lambda x: -x[1][1])
    top_countries = [
        SummaryCountryInfo(country=full_name, iso_country=iso, count=count)
        for iso, (full_name, count) in sorted_countries[:5]
    ]
    other_countries_count = len(sorted_countries) - len(top_countries)

    # Largest 5 direct children by descendant count
    children_with_counts = [
        (child, _count_descendants(child))
        for child in tree.root.children
    ]
    children_with_counts.sort(key=lambda x: -x[1])
    largest_children = [
        SummaryChildInfo(id=child.company_id, name=child.company_name, descendants=count)
        for child, count in children_with_counts[:5]
    ]

    # Ultimate parent
    ultimate_parent: SummaryCompanyInfo | None = None
    if response.ultimate_parent_path and len(response.ultimate_parent_path) > 1:
        parent_info = response.ultimate_parent_path[0]
        ultimate_parent = SummaryCompanyInfo(id=parent_info.id, name=parent_info.name)

    return CorporateTreeSummaryResult(
        tree_size=tree_size,
        tree_truncated=tree.is_truncated,
        direct_children=len(tree.root.children),
        depth=_max_depth(tree.root, 0),
        ultimate_parent=ultimate_parent,
        by_type=by_type,
        top_countries=top_countries,
        other_countries_count=other_countries_count,
        largest_children=largest_children,
    )
