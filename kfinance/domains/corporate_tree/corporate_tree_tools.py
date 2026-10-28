from collections import Counter, defaultdict, deque
from textwrap import dedent
from typing import Type

import httpx2
from pydantic import BaseModel, Field, field_validator

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.corporate_tree.corporate_tree_models import (
    CorporateTreeNode,
    CorporateTreeResponse,
    CorporateTreeSearchResult,
    MaxTreeDepth,
    SearchMatch,
    SearchSummary,
    TreeRelationshipStatus,
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
        Get the ownership paths from each identifier up to its ultimate parents.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - Pass a ticker as given. Otherwise pass the company's full name with its legal suffix.
        - Each path runs from the queried company to an ultimate parent. A company owned through several chains has several paths; one with no controlling parent has a single path holding only itself.
        - Each element's relationship_type is how it is owned by the next element. The last element has a null parent_company_id and relationship_type.
        - Only current, controlling relationships are included. To check whether a company used to be owned by a parent, call search_corporate_tree_from_identifiers on the parent with relationship_status=["current", "prior"].
        - Only companies and similar institutions can be queried; indexes, funds, commodities, yield curves and assets/products return an error.

        Examples:
        Query: "Who is the ultimate parent of Instagram?"
        Function: get_ultimate_parent_paths_from_identifiers(identifiers=["Instagram"])

        Query: "Show the direct and the top-level owners of YouTube and WhatsApp"
        Function: get_ultimate_parent_paths_from_identifiers(identifiers=["YouTube", "WhatsApp"])

        Query: "Is Instagram still owned by Meta?"
        Function: get_ultimate_parent_paths_from_identifiers(identifiers=["Instagram"])
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.OnlyStaffPermission}

    async def _arun(self, identifiers: list[str]) -> GetUltimateParentPathsFromIdentifiersResp:
        """"""
        return await get_ultimate_parent_paths_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def get_ultimate_parent_paths_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx2.AsyncClient,
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
    httpx_client: httpx2.AsyncClient,
) -> UltimateParentPathsResponse:
    """Fetch every path from a single company up to its ultimate parents."""
    resp = await httpx_client.get(url=f"/corporate_tree/{company_id}/ultimate_parent_paths")
    resp.raise_for_status()
    return UltimateParentPathsResponse.model_validate(resp.json())


class SearchCorporateTreeFromIdentifiersArgs(ToolArgsWithIdentifiers):
    relationship_type: list[TreeRelationshipType] | None = Field(
        default=None,
        description="When the question names a kind of entity (subsidiaries, merged businesses, investment arms, government entities), pass the matching type, also for prior relationships. Omit it when every entity is wanted.",
    )
    country_iso_code: list[str] | None = Field(
        default=None,
        description="ISO 3166-1 alpha-3 codes only, e.g. ['USA', 'DEU']. Convert names and two-letter codes first (Germany, DE -> DEU).",
    )
    max_depth: MaxTreeDepth | None = Field(
        default=None,
        description="Levels below the company to search; 1 means direct relationships only. Omit to search the whole tree.",
    )
    relationship_status: list[TreeRelationshipStatus] | None = Field(
        default=None,
        description="Whether a company is still under the queried company, matched against relationship_status_to_queried_company. Defaults to ['current']. Pass ['prior'] when former, previous, divested or sold entities are asked for, or ['current', 'prior'] for both.",
    )
    limit: int | None = Field(
        default=50,
        description="Maximum matches to return per identifier. Pass null for every match, which can be a very large response on a big tree.",
        ge=1,
    )

    @field_validator("country_iso_code")
    @classmethod
    def validate_country_iso_code(cls, v: list[str] | None) -> list[str] | None:
        """Reject invalid codes."""
        return _validated_alpha_3(v)

    @field_validator("relationship_type", "relationship_status")
    @classmethod
    def empty_list_means_omitted(cls, v: list | None) -> list | None:
        """Treat an empty filter list as if the filter had not been passed."""
        return v or None


class SearchCorporateTreeFromIdentifiersResp(
    ToolRespWithIdInfoAndErrors[CorporateTreeSearchResult]
):
    pass


class SearchCorporateTreeFromIdentifiers(KfinanceTool):
    name: str = "search_corporate_tree_from_identifiers"
    description: str = dedent("""
        Search the companies below a company in its corporate tree. Filters combine with AND; the values within one filter combine with OR.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - Pass a ticker as given. Otherwise pass the company's full name with its legal suffix.
        - Only controlling relationships are included; minority and other non-controlling stakes are absent.
        - Only companies and similar institutions can be queried; indexes, funds, commodities, yield curves and assets/products return an error.
        - The queried company is never a match. To look upward from it, use get_ultimate_parent_paths_from_identifiers.
        - There is no name filter: pick matches by company_name. If summary.total_matches exceeds the matches returned, raise limit, pass limit=null for all of them, or narrow the filters.
        - A company with several parents appears once per parent; summary.distinct_companies counts the companies.
        - relationship_status matches relationship_status_to_queried_company. A company moved from one parent to another within the tree stays current for every row, while a current unit under a divested company counts as prior. relationship_status_to_direct_parent reports each row's own edge to parent_company_id, so a re-parented company's row for its old parent shows prior there.
        - When summary.search_was_depth_limited is true, the summary's *_searched counts cover only the searched depth.

        Examples:
        Query: "What subsidiaries does Microsoft have in Germany?"
        Function: search_corporate_tree_from_identifiers(identifiers=["Microsoft"], country_iso_code=["DEU"], relationship_type=["subsidiary_or_operating_unit"])

        Query: "Which subsidiaries has Pfizer divested?"
        Function: search_corporate_tree_from_identifiers(identifiers=["PFE"], relationship_type=["subsidiary_or_operating_unit"], relationship_status=["prior"])

        Query: "Which businesses has Oracle absorbed directly?"
        Function: search_corporate_tree_from_identifiers(identifiers=["ORCL"], relationship_type=["merged_entity"], max_depth=1)

        Query: "Was Motorola Mobility ever part of Alphabet?"
        Function: search_corporate_tree_from_identifiers(identifiers=["GOOGL"], relationship_status=["current", "prior"], limit=null)
    """).strip()
    args_schema: Type[BaseModel] = SearchCorporateTreeFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.OnlyStaffPermission}

    async def _arun(
        self,
        identifiers: list[str],
        relationship_type: list[TreeRelationshipType] | None = None,
        country_iso_code: list[str] | None = None,
        max_depth: int | None = None,
        relationship_status: list[TreeRelationshipStatus] | None = None,
        limit: int | None = 50,
    ) -> SearchCorporateTreeFromIdentifiersResp:
        """"""
        return await search_corporate_tree_from_identifiers(
            identifiers=identifiers,
            relationship_type=relationship_type,
            country_iso_code=country_iso_code,
            max_depth=max_depth,
            relationship_status=relationship_status,
            limit=limit,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def search_corporate_tree_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx2.AsyncClient,
    relationship_type: list[TreeRelationshipType] | None = None,
    country_iso_code: list[str] | None = None,
    max_depth: int | None = None,
    relationship_status: list[TreeRelationshipStatus] | None = None,
    limit: int | None = 50,
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
                max_depth=max_depth,
                relationship_status=relationship_status,
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


def _without_blanks(values: list[str] | None) -> list[str] | None:
    """Strip each value and drop the blanks. A filter left with nothing is treated as omitted."""
    if values is None:
        return None
    stripped = [value.strip() for value in values if value.strip()]
    return stripped or None


def _validated_alpha_3(codes: list[str] | None) -> list[str] | None:
    """Reject anything that is not an ISO 3166-1 alpha-3 code, rather than matching nothing."""
    codes = _without_blanks(codes)
    if codes is None:
        return None

    invalid = [code for code in codes if not (len(code) == 3 and code.isascii() and code.isalpha())]
    if invalid:
        raise ValueError(
            f"country_iso_code takes ISO 3166-1 alpha-3 codes (three letters) only; got {invalid}. "
            "Convert to alpha-3 before calling, e.g. Germany or DE -> DEU, United Kingdom or GB -> GBR."
        )
    return codes


def _current_chain_company_ids(root_company_id: int, nodes: list[CorporateTreeNode]) -> set[int]:
    """Company ids reachable from the queried company through current relationships only."""
    children: dict[int, list[int]] = defaultdict(list)
    for node in nodes:
        if node.relationship_status is TreeRelationshipStatus.current:
            children[node.parent_company_id].append(node.company.company_id)

    reachable = {root_company_id}
    queue = deque([root_company_id])
    while queue:
        for child_id in children[queue.popleft()]:
            if child_id not in reachable:
                reachable.add(child_id)
                queue.append(child_id)
    return reachable


def _relationship_status_to_queried_company(
    node: CorporateTreeNode, current_chain_company_ids: set[int]
) -> TreeRelationshipStatus:
    """Whether the node's company is still under the queried company.

    A company moved from one parent to another inside the tree has a prior row for the old
    parent and a current row for the new one, and is still under the queried company through
    the latter. A current relationship hanging below a divested ancestor has no current
    chain left, so it comes back as prior.
    """
    if node.company.company_id in current_chain_company_ids:
        return TreeRelationshipStatus.current
    return TreeRelationshipStatus.prior


def _node_matches(
    node: CorporateTreeNode,
    relationship_statuses: list[TreeRelationshipStatus],
    relationship_status_to_queried_company: TreeRelationshipStatus,
    relationship_types: list[TreeRelationshipType] | None,
    country_iso_codes: list[str] | None,
) -> bool:
    """Whether a node satisfies every supplied filter. Country matching is case-insensitive."""
    # The status filter tests whether the company is still under the queried company, not the
    # node's own edge: a re-parented company counts as current even on the row for its old parent.
    if relationship_status_to_queried_company not in relationship_statuses:
        return False

    if relationship_types is not None and node.relationship_type not in relationship_types:
        return False

    if country_iso_codes is not None:
        iso_country = node.company.iso_country
        if iso_country is None:
            return False
        if not any(iso_country.casefold() == code.casefold() for code in country_iso_codes):
            return False

    return True


async def fetch_and_search_corporate_tree(
    company_id: int,
    httpx_client: httpx2.AsyncClient,
    relationship_type: list[TreeRelationshipType] | None = None,
    country_iso_code: list[str] | None = None,
    max_depth: int | None = None,
    relationship_status: list[TreeRelationshipStatus] | None = None,
    limit: int | None = 50,
) -> CorporateTreeSearchResult:
    """Fetch the corporate tree for a single company and search it."""
    statuses = relationship_status or [TreeRelationshipStatus.current]
    # Applied here as well as on the args model, so direct callers behave the same way.
    country_iso_code = _validated_alpha_3(country_iso_code)
    relationship_type = relationship_type or None
    response = await fetch_corporate_tree(
        company_id=company_id,
        httpx_client=httpx_client,
        # The endpoint is all-or-nothing, so prior relationships have to be fetched before
        # they can be filtered on.
        include_prior=TreeRelationshipStatus.prior in statuses,
        max_depth=max_depth,
    )

    current_chain = _current_chain_company_ids(response.root.company_id, response.nodes)
    # The API already applied max_depth, so there is no depth filtering left to do here.
    matches = [
        node
        for node in response.nodes
        if _node_matches(
            node,
            relationship_statuses=statuses,
            relationship_status_to_queried_company=_relationship_status_to_queried_company(
                node, current_chain
            ),
            relationship_types=relationship_type,
            country_iso_codes=country_iso_code,
        )
    ]

    shown = matches[:limit]
    return CorporateTreeSearchResult(
        queried_company=response.root,
        matches=[
            SearchMatch(
                company_id=node.company.company_id,
                company_name=node.company.company_name,
                company_type=node.company.company_type,
                country=node.company.country,
                iso_country=node.company.iso_country,
                parent_company_id=node.parent_company_id,
                level=node.level,
                relationship_type=node.relationship_type,
                relationship_status_to_direct_parent=node.relationship_status,
                relationship_status_to_queried_company=_relationship_status_to_queried_company(
                    node, current_chain
                ),
            )
            for node in shown
        ],
        summary=SearchSummary(
            total_matches=len(matches),
            distinct_companies=len({node.company.company_id for node in matches}),
            showing=len(shown),
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
    httpx_client: httpx2.AsyncClient,
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
