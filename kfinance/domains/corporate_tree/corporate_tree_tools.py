from collections import Counter, defaultdict
from textwrap import dedent
from typing import Type

import httpx
from pydantic import BaseModel, Field

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.corporate_tree.corporate_tree_models import (
    CompanyInfo,
    CorporateTreeNode,
    CorporateTreeResponse,
    TreeRelationshipStatus,
    TreeRelationshipType,
    UltimateParentPathsResponse,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithIdInfoAndErrors,
)


# How many countries and direct children to report in a tree summary.
_TOP_N = 5


# --- Fetchers ---


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


async def fetch_ultimate_parent_paths(
    company_id: int,
    httpx_client: httpx.AsyncClient,
) -> UltimateParentPathsResponse:
    """Fetch every path from a single company up to its ultimate parents."""
    resp = await httpx_client.get(url=f"/corporate_tree/{company_id}/ultimate_parent_paths")
    resp.raise_for_status()
    return UltimateParentPathsResponse.model_validate(resp.json())


# --- Graph helpers ---
#
# `level` on a node is the shallowest depth at which the relationship was found, so it is not
# always `parent.level + 1`. These helpers rebuild the graph by following `parent_company_id`
# instead of doing arithmetic on `level`.


def _children_by_parent(nodes: list[CorporateTreeNode]) -> dict[int, set[int]]:
    """Map each parent company id to the set of its child company ids."""
    children_by_parent: dict[int, set[int]] = defaultdict(set)
    for node in nodes:
        children_by_parent[node.parent_company_id].add(node.company.company_id)
    return children_by_parent


def _descendant_counts(
    root_company_id: int, children_by_parent: dict[int, set[int]]
) -> dict[int, int]:
    """Count the distinct companies below every company reachable from root_company_id.

    Each company's reachable set is `{itself} | union(reachable sets of its children)`, computed
    once and reused by every parent, rather than re-traversed once per direct child of the root.
    It has to be a union and not a sum of counts: the tree is a DAG, so two children's reachable
    sets can overlap and adding their counts would double-count the shared companies.

    Each set is held as an integer bitmask over dense bit positions, because company ids are
    around 1.8e9 and would otherwise make the masks enormous. That keeps a union to a machine-word
    OR instead of copying set elements up the graph, which matters on trees that are both wide and
    deep.
    """
    # Depth-first post-order, iterative because trees can be dozens of levels deep. A company is
    # appended only after all of its children, so one forward pass over `order` sees children
    # before parents.
    bit_of_company: dict[int, int] = {}
    order: list[int] = []
    stack: list[tuple[int, bool]] = [(root_company_id, False)]
    while stack:
        company_id, children_expanded = stack.pop()
        if children_expanded:
            order.append(company_id)
        elif company_id not in bit_of_company:
            bit_of_company[company_id] = 1 << len(bit_of_company)
            stack.append((company_id, True))
            stack.extend(
                (child_company_id, False)
                for child_company_id in children_by_parent.get(company_id, ())
                if child_company_id not in bit_of_company
            )

    # The edge list can contain cycles: the API's cycle guard applies per path, and the response
    # unions relationships discovered along different paths, so two routes can together close a
    # loop. A single post-order pass would then miss the edges that run backwards, so iterate to a
    # fixpoint. On an acyclic tree that is one pass to fill and one to confirm nothing grew.
    reachable = dict(bit_of_company)
    grew = True
    while grew:
        grew = False
        for company_id in order:
            mask = reachable[company_id]
            for child_company_id in children_by_parent.get(company_id, ()):
                mask |= reachable[child_company_id]
            if mask != reachable[company_id]:
                reachable[company_id] = mask
                grew = True

    # Each mask includes the company itself, which is not one of its own descendants.
    return {company_id: mask.bit_count() - 1 for company_id, mask in reachable.items()}


# --- Response models ---


class SearchNodeResult(BaseModel):
    """A single relationship returned from a corporate tree search."""

    company_id: int
    company_name: str
    country: str | None = None
    iso_country: str | None = None
    parent_company_id: int
    level: int
    relationship_type: TreeRelationshipType
    relationship_status: TreeRelationshipStatus


class SearchSummary(BaseModel):
    """Summary metadata about the search results and the tree they were drawn from."""

    total_matches: int = Field(
        description="Matching relationships. A company owned through several parents matches once per parent."
    )
    distinct_companies: int = Field(description="Distinct companies among the matches.")
    showing: int = Field(description="Matches included in `nodes`, capped by the `limit` argument.")
    matches_by_level: dict[str, int]
    tree_total_companies: int
    tree_total_edges: int
    tree_max_depth: int
    truncated_company_ids: list[int] = Field(
        description="Companies at the max_depth limit whose children were not searched. Empty when the whole tree was searched."
    )


class CorporateTreeSearchResult(BaseModel):
    """Search results from a company's corporate tree."""

    root: CompanyInfo
    nodes: list[SearchNodeResult]
    summary: SearchSummary


class SummaryCountryInfo(BaseModel):
    """Country entry in the top_countries list."""

    country: str | None = None
    iso_country: str | None = None
    company_count: int


class SummaryChildInfo(BaseModel):
    """A direct child with the number of companies below it."""

    company_id: int
    company_name: str
    descendant_count: int


class CorporateTreeSummaryResult(BaseModel):
    """Summary statistics for a corporate tree."""

    root: CompanyInfo
    total_companies: int = Field(description="Distinct companies in the tree, counting the root.")
    total_edges: int = Field(
        description="Parent-child relationships in the tree. Exceeds total_companies when companies have multiple parents."
    )
    max_depth: int
    direct_children_count: int
    companies_per_level: dict[str, int] = Field(
        description="Companies at each level, each counted once at its shallowest level. Excludes the root."
    )
    edges_per_relationship_type: dict[str, int]
    edges_per_relationship_status: dict[str, int]
    top_countries: list[SummaryCountryInfo]
    other_countries_count: int
    largest_children: list[SummaryChildInfo]
    truncated_company_ids: list[int] = Field(
        description="Companies at the max_depth limit whose children are not counted. Empty when the whole tree was retrieved."
    )


# --- Tool 1: Get Ultimate Parent Paths ---


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


# --- Tool 2: Search Corporate Tree ---


class SearchCorporateTreeArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    relationship_type: list[TreeRelationshipType] | None = Field(
        default=None,
        description="Filter by relationship type(s). Nodes matching ANY of the listed types are included.",
    )
    iso_country: list[str] | None = Field(
        default=None,
        description="Countries to filter by, as ISO 3166-1 alpha-3 codes only (e.g., ['USA', 'GBR', 'DEU']). Full country names are not accepted. Nodes in ANY of the listed countries are included.",
    )
    name: list[str] | None = Field(
        default=None,
        description="Substring(s) to match against company names (case-insensitive). Nodes matching ANY of the listed substrings are included.",
    )
    max_depth: int | None = Field(
        default=None,
        description="How many levels below the company to search. Omit to search the entire tree. Use max_depth=1 to search direct subsidiaries only.",
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
        - Returns up to `limit` matching nodes per identifier (default 50). `summary.total_matches` reports how many matched in total.
        - The queried company itself is never a match; only the companies below it are searched.
        - Set max_depth to limit how deep to search. E.g. max_depth=1 searches direct children only. Omit it to search the whole tree.
        - Set include_prior=true to also include historical relationships that are no longer active.
        - A company owned through several parents appears once per parent, each with its own parent_company_id. `summary.distinct_companies` counts the underlying companies.
        - iso_country takes ISO 3166-1 alpha-3 codes only. Convert country names to codes before calling, e.g. Germany -> DEU.

        Examples:
        Query: "What subsidiaries does Microsoft have in Germany?"
        Function: search_corporate_tree_from_identifiers(identifiers=["Microsoft"], iso_country=["DEU"], relationship_type=["subsidiary_or_operating_unit"])

        Query: "Find all entities named 'Capital' or 'Global' under JPMorgan"
        Function: search_corporate_tree_from_identifiers(identifiers=["JPM"], name=["Capital", "Global"])

        Query: "List the direct subsidiaries of Apple"
        Function: search_corporate_tree_from_identifiers(identifiers=["Apple"], max_depth=1, relationship_type=["subsidiary_or_operating_unit"])

        Query: "Find all subsidiaries and investment arms of S&P Global in the US, UK, and India"
        Function: search_corporate_tree_from_identifiers(identifiers=["SPGI"], relationship_type=["subsidiary_or_operating_unit", "investment_arm"], iso_country=["USA", "GBR", "IND"])
    """).strip()
    args_schema: Type[BaseModel] = SearchCorporateTreeArgs
    accepted_permissions: set[Permission] | None = None

    async def _arun(
        self,
        identifiers: list[str],
        relationship_type: list[TreeRelationshipType] | None = None,
        iso_country: list[str] | None = None,
        name: list[str] | None = None,
        max_depth: int | None = None,
        include_prior: bool = False,
        limit: int = 50,
    ) -> SearchCorporateTreeFromIdentifiersResp:
        """"""
        return await search_corporate_tree_from_identifiers(
            identifiers=identifiers,
            relationship_type=relationship_type,
            iso_country=iso_country,
            name=name,
            max_depth=max_depth,
            include_prior=include_prior,
            limit=limit,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def search_corporate_tree_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
    relationship_type: list[TreeRelationshipType] | None = None,
    iso_country: list[str] | None = None,
    name: list[str] | None = None,
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
                iso_country=iso_country,
                name=name,
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
    relationship_types: set[TreeRelationshipType] | None,
    iso_countries: set[str] | None,
    names: list[str] | None,
) -> bool:
    """Whether a node satisfies every supplied filter.

    `iso_countries` and `names` are expected pre-casefolded by the caller.
    """
    if relationship_types is not None and node.relationship_type not in relationship_types:
        return False

    if iso_countries is not None:
        # Matched against the ISO alpha-3 code only; the full country name is not consulted.
        if node.company.iso_country is None:
            return False
        if node.company.iso_country.casefold() not in iso_countries:
            return False

    if names is not None:
        node_name = node.company.company_name.casefold()
        if not any(name in node_name for name in names):
            return False

    return True


async def fetch_and_search_corporate_tree(
    company_id: int,
    httpx_client: httpx.AsyncClient,
    relationship_type: list[TreeRelationshipType] | None = None,
    iso_country: list[str] | None = None,
    name: list[str] | None = None,
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

    relationship_types = set(relationship_type) if relationship_type else None
    iso_countries = {value.casefold() for value in iso_country} if iso_country else None
    names = [value.casefold() for value in name] if name else None

    # The API already applied max_depth, so there is no depth filtering left to do here.
    matches = [
        node
        for node in response.nodes
        if _node_matches(node, relationship_types, iso_countries, names)
    ]

    return CorporateTreeSearchResult(
        root=response.root,
        nodes=[
            SearchNodeResult(
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
            tree_total_companies=response.summary.total_companies,
            tree_total_edges=response.summary.total_edges,
            tree_max_depth=response.summary.max_depth,
            truncated_company_ids=(
                response.truncation.truncated_company_ids if response.truncation else []
            ),
        ),
    )


# --- Tool 3: Get Corporate Tree Summary ---


class CorporateTreeSummaryArgs(ToolArgsWithIdentifiers):
    include_prior: bool = Field(
        default=False,
        description="If true, include prior/historical relationships in the counts. By default only current relationships are included.",
    )


class GetCorporateTreeSummaryFromIdentifiersResp(
    ToolRespWithIdInfoAndErrors[CorporateTreeSummaryResult]
):
    pass


class GetCorporateTreeSummaryFromIdentifiers(KfinanceTool):
    name: str = "get_corporate_tree_summary_from_identifiers"
    description: str = dedent("""
        Get summary statistics about the corporate tree below a company.

        Returns the total number of companies and relationships, a breakdown by level, by relationship type (subsidiary, merged entity, investment arm, affiliated government institution) and by country, plus the direct children with the most companies beneath them.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - The tree is a graph, not a strict hierarchy: a company can be owned through several parents, which is why total_edges can exceed total_companies and why the descendant counts in largest_children can overlap and need not sum to total_companies.
        - Covers only the companies below the queried company. To find who owns it, use get_ultimate_parent_paths_from_identifiers.
        - Set include_prior=true to also count historical relationships that are no longer active.

        Examples:
        Query: "How many subsidiaries does Berkshire Hathaway have?"
        Function: get_corporate_tree_summary_from_identifiers(identifiers=["Berkshire Hathaway"])

        Query: "Compare the corporate tree sizes of Apple and Microsoft"
        Function: get_corporate_tree_summary_from_identifiers(identifiers=["Apple", "Microsoft"])
    """).strip()
    args_schema: Type[BaseModel] = CorporateTreeSummaryArgs
    accepted_permissions: set[Permission] | None = None

    async def _arun(
        self, identifiers: list[str], include_prior: bool = False
    ) -> GetCorporateTreeSummaryFromIdentifiersResp:
        """"""
        return await get_corporate_tree_summary_from_identifiers(
            identifiers=identifiers,
            include_prior=include_prior,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def get_corporate_tree_summary_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
    include_prior: bool = False,
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
                include_prior=include_prior,
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
    include_prior: bool = False,
) -> CorporateTreeSummaryResult:
    """Fetch the whole corporate tree for a single company and summarize it."""
    response = await fetch_corporate_tree(
        company_id=company_id,
        httpx_client=httpx_client,
        include_prior=include_prior,
    )

    # A company can appear at several levels, so bucket each one at its shallowest. The buckets
    # then sum to total_companies - 1, the root having no level of its own.
    shallowest_level_by_company: dict[int, int] = {}
    for node in response.nodes:
        node_company_id = node.company.company_id
        shallowest_level_by_company[node_company_id] = min(
            node.level, shallowest_level_by_company.get(node_company_id, node.level)
        )

    # Countries are counted per distinct company rather than per relationship.
    country_by_company: dict[int, tuple[str | None, str | None]] = {
        response.root.company_id: (response.root.country, response.root.iso_country)
    }
    for node in response.nodes:
        country_by_company[node.company.company_id] = (
            node.company.country,
            node.company.iso_country,
        )
    company_counts_by_country = Counter(country_by_company.values())
    ranked_countries = sorted(
        company_counts_by_country.items(),
        key=lambda item: (-item[1], item[0][1] or "", item[0][0] or ""),
    )

    children_by_parent = _children_by_parent(response.nodes)
    direct_child_company_ids = children_by_parent.get(response.root.company_id, set())
    company_names = {node.company.company_id: node.company.company_name for node in response.nodes}
    descendant_counts = _descendant_counts(response.root.company_id, children_by_parent)
    ranked_children = sorted(
        (
            SummaryChildInfo(
                company_id=child_company_id,
                company_name=company_names[child_company_id],
                descendant_count=descendant_counts[child_company_id],
            )
            for child_company_id in direct_child_company_ids
        ),
        key=lambda child: (-child.descendant_count, child.company_id),
    )

    return CorporateTreeSummaryResult(
        root=response.root,
        total_companies=response.summary.total_companies,
        total_edges=response.summary.total_edges,
        max_depth=response.summary.max_depth,
        direct_children_count=len(direct_child_company_ids),
        companies_per_level={
            str(level): count
            for level, count in sorted(Counter(shallowest_level_by_company.values()).items())
        },
        edges_per_relationship_type=dict(
            sorted(Counter(node.relationship_type.value for node in response.nodes).items())
        ),
        edges_per_relationship_status=dict(
            sorted(Counter(node.relationship_status.value for node in response.nodes).items())
        ),
        top_countries=[
            SummaryCountryInfo(country=country, iso_country=iso_country, company_count=count)
            for (country, iso_country), count in ranked_countries[:_TOP_N]
        ],
        other_countries_count=max(len(company_counts_by_country) - _TOP_N, 0),
        largest_children=ranked_children[:_TOP_N],
        truncated_company_ids=(
            response.truncation.truncated_company_ids if response.truncation else []
        ),
    )
