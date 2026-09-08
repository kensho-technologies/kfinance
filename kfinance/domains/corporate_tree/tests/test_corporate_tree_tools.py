import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.conftest import SPGI_COMPANY_ID, SPGI_ID_TRIPLE
from kfinance.domains.corporate_tree.corporate_tree_models import TreeRelationshipType
from kfinance.domains.corporate_tree.corporate_tree_tools import (
    fetch_and_search_corporate_tree,
    fetch_corporate_tree,
    fetch_ultimate_parent_paths,
    get_ultimate_parent_paths_from_identifiers,
    search_corporate_tree_from_identifiers,
)


# --- Test fixtures ---
#
# SAMPLE_TREE_RESPONSE is copied from the backend's own snapshot
# (django_app/tests/integration/__snapshots__/test_views_with_mock_data.ambr,
# TestCorporateTree.test_corporate_tree_snapshot), so it exercises the awkward cases the real API
# produces:
#   - 267302130 sits under the root twice, once per relationship type.
#   - 8536775 sits under two different parents (34482 and 267302130).
#   - 13651733 appears at level 1 and again at level 3, under a different parent.
# 9 distinct companies (counting the root) across 12 edges.

SNL = 34482
IHS_MARKIT = 13651733
NJ_DATA_CENTER = 267302130
JD_POWER = 1532723
JUVENILE_RETAIL = 8536775
OSTTRA = 1805062246
KENSHO = 251994106
MCGRAW_HILL_EDUCATION = 1067110

_USA = {"country": "United States", "iso_country": "USA"}
_GBR = {"country": "United Kingdom", "iso_country": "GBR"}

SPGI_ROOT = {"company_id": SPGI_COMPANY_ID, "company_name": "S&P Global Inc.", **_USA}

SAMPLE_TREE_RESPONSE = {
    "root": SPGI_ROOT,
    "nodes": [
        {
            "company": {"company_id": SNL, "company_name": "SNL Financial LC", **_USA},
            "level": 1,
            "parent_company_id": SPGI_COMPANY_ID,
            "relationship_status": "current",
            "relationship_type": "subsidiary_or_operating_unit",
        },
        {
            "company": {"company_id": IHS_MARKIT, "company_name": "IHS Markit Ltd.", **_GBR},
            "level": 1,
            "parent_company_id": SPGI_COMPANY_ID,
            "relationship_status": "current",
            "relationship_type": "subsidiary_or_operating_unit",
        },
        {
            "company": {
                "company_id": NJ_DATA_CENTER,
                "company_name": "McGraw Hill Financial, Inc., New Jersey Data Center",
                **_USA,
            },
            "level": 1,
            "parent_company_id": SPGI_COMPANY_ID,
            "relationship_status": "current",
            "relationship_type": "subsidiary_or_operating_unit",
        },
        {
            "company": {
                "company_id": NJ_DATA_CENTER,
                "company_name": "McGraw Hill Financial, Inc., New Jersey Data Center",
                **_USA,
            },
            "level": 1,
            "parent_company_id": SPGI_COMPANY_ID,
            "relationship_status": "current",
            "relationship_type": "merged_entity",
        },
        {
            "company": {"company_id": JD_POWER, "company_name": "J.D. Power", **_USA},
            "level": 2,
            "parent_company_id": SNL,
            "relationship_status": "current",
            "relationship_type": "subsidiary_or_operating_unit",
        },
        {
            "company": {
                "company_id": JUVENILE_RETAIL,
                "company_name": "The McGraw-Hill Companies, Juvenile Retail Publishing Businesses",
                **_USA,
            },
            "level": 2,
            "parent_company_id": SNL,
            "relationship_status": "current",
            "relationship_type": "subsidiary_or_operating_unit",
        },
        {
            "company": {"company_id": OSTTRA, "company_name": "Osttra Group Ltd.", **_GBR},
            "level": 2,
            "parent_company_id": IHS_MARKIT,
            "relationship_status": "current",
            "relationship_type": "investment_arm",
        },
        {
            "company": {
                "company_id": JUVENILE_RETAIL,
                "company_name": "The McGraw-Hill Companies, Juvenile Retail Publishing Businesses",
                **_USA,
            },
            "level": 2,
            "parent_company_id": NJ_DATA_CENTER,
            "relationship_status": "current",
            "relationship_type": "subsidiary_or_operating_unit",
        },
        {
            "company": {"company_id": KENSHO, "company_name": "Kensho Technologies, Inc.", **_USA},
            "level": 2,
            "parent_company_id": NJ_DATA_CENTER,
            "relationship_status": "current",
            "relationship_type": "merged_entity",
        },
        {
            "company": {"company_id": KENSHO, "company_name": "Kensho Technologies, Inc.", **_USA},
            "level": 2,
            "parent_company_id": NJ_DATA_CENTER,
            "relationship_status": "current",
            "relationship_type": "subsidiary_or_operating_unit",
        },
        {
            "company": {"company_id": IHS_MARKIT, "company_name": "IHS Markit Ltd.", **_GBR},
            "level": 3,
            "parent_company_id": JD_POWER,
            "relationship_status": "current",
            "relationship_type": "subsidiary_or_operating_unit",
        },
        {
            "company": {
                "company_id": MCGRAW_HILL_EDUCATION,
                "company_name": "McGraw-Hill Education, Inc.",
                **_USA,
            },
            "level": 3,
            "parent_company_id": JUVENILE_RETAIL,
            "relationship_status": "current",
            "relationship_type": "subsidiary_or_operating_unit",
        },
    ],
    "summary": {"max_depth": 3, "total_companies": 9, "total_edges": 12},
    # The API omits the "truncation" key entirely when the whole tree was returned.
}

# The same tree fetched with max_depth=1: the three level-1 companies are reported as truncated.
SAMPLE_TREE_RESPONSE_TRUNCATED = {
    "root": SPGI_ROOT,
    "nodes": SAMPLE_TREE_RESPONSE["nodes"][:4],
    "summary": {"max_depth": 1, "total_companies": 4, "total_edges": 4},
    "truncation": {"truncated_company_ids": [SNL, IHS_MARKIT, NJ_DATA_CENTER]},
}

# A tree whose single subsidiary has no country recorded.
SAMPLE_TREE_RESPONSE_NO_COUNTRY = {
    "root": SPGI_ROOT,
    "nodes": [
        {
            "company": {
                "company_id": KENSHO,
                "company_name": "Kensho Technologies, Inc.",
                "country": None,
                "iso_country": None,
            },
            "level": 1,
            "parent_company_id": SPGI_COMPANY_ID,
            "relationship_status": "current",
            "relationship_type": "subsidiary_or_operating_unit",
        }
    ],
    "summary": {"max_depth": 1, "total_companies": 2, "total_edges": 1},
}

# A tree reaching level 10, used to check that level keys are ordered numerically rather than
# lexicographically ("10" must not sort before "2").
SAMPLE_DEEP_TREE_RESPONSE = {
    "root": SPGI_ROOT,
    "nodes": [
        {
            "company": {"company_id": 1000 + level, "company_name": f"Sub {level}", **_USA},
            "level": level,
            "parent_company_id": SPGI_COMPANY_ID if level == 1 else 1000 + level - 1,
            "relationship_status": "current",
            "relationship_type": "subsidiary_or_operating_unit",
        }
        for level in range(1, 11)
    ],
    "summary": {"max_depth": 10, "total_companies": 11, "total_edges": 10},
}

# Copied from the backend snapshot TestUltimateParentPaths.test_ultimate_parent_paths_snapshot:
# McGraw-Hill Education is owned through two distinct chains, both ending at S&P Global.
MULTI_PATHS_RESPONSE = {
    "paths": [
        [
            {
                "company_id": MCGRAW_HILL_EDUCATION,
                "company_name": "McGraw-Hill Education, Inc.",
                **_USA,
                "parent_company_id": JUVENILE_RETAIL,
                "relationship_type": "subsidiary_or_operating_unit",
            },
            {
                "company_id": JUVENILE_RETAIL,
                "company_name": "The McGraw-Hill Companies, Juvenile Retail Publishing Businesses",
                **_USA,
                "parent_company_id": SNL,
                "relationship_type": "subsidiary_or_operating_unit",
            },
            {
                "company_id": SNL,
                "company_name": "SNL Financial LC",
                **_USA,
                "parent_company_id": SPGI_COMPANY_ID,
                "relationship_type": "subsidiary_or_operating_unit",
            },
            {
                **SPGI_ROOT,
                "parent_company_id": None,
                "relationship_type": None,
            },
        ],
        [
            {
                "company_id": MCGRAW_HILL_EDUCATION,
                "company_name": "McGraw-Hill Education, Inc.",
                **_USA,
                "parent_company_id": JUVENILE_RETAIL,
                "relationship_type": "subsidiary_or_operating_unit",
            },
            {
                "company_id": JUVENILE_RETAIL,
                "company_name": "The McGraw-Hill Companies, Juvenile Retail Publishing Businesses",
                **_USA,
                "parent_company_id": NJ_DATA_CENTER,
                "relationship_type": "subsidiary_or_operating_unit",
            },
            {
                "company_id": NJ_DATA_CENTER,
                "company_name": "McGraw Hill Financial, Inc., New Jersey Data Center",
                **_USA,
                "parent_company_id": SPGI_COMPANY_ID,
                "relationship_type": "subsidiary_or_operating_unit",
            },
            {
                **SPGI_ROOT,
                "parent_company_id": None,
                "relationship_type": None,
            },
        ],
    ]
}

# S&P Global has no controlling parent, so it is its own ultimate parent.
SINGLE_PATH_RESPONSE = {
    "paths": [[{**SPGI_ROOT, "parent_company_id": None, "relationship_type": None}]]
}

API_BASE = "https://kfinance.kensho.com/api/v1"
CORPORATE_TREE_URL = f"{API_BASE}/corporate_tree/{SPGI_COMPANY_ID}"
ULTIMATE_PARENT_PATHS_URL = f"{CORPORATE_TREE_URL}/ultimate_parent_paths"


# --- Tests for the fetchers ---


class TestFetchCorporateTree:
    @pytest.mark.asyncio
    async def test_fetch_corporate_tree(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """WHEN we fetch a corporate tree THEN we get a valid CorporateTreeResponse."""
        httpx_mock.add_response(
            method="GET",
            url=f"{CORPORATE_TREE_URL}?include_prior=false",
            json=SAMPLE_TREE_RESPONSE,
        )

        resp = await fetch_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
        )

        assert resp.root.company_id == SPGI_COMPANY_ID
        assert len(resp.nodes) == 12
        assert resp.summary.total_companies == 9
        assert resp.summary.total_edges == 12
        # The API omits the key entirely when nothing was truncated.
        assert resp.truncation is None

    @pytest.mark.asyncio
    async def test_fetch_corporate_tree_with_include_prior_and_max_depth(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """WHEN include_prior and max_depth are given THEN both reach the request URL."""
        httpx_mock.add_response(
            method="GET",
            url=f"{CORPORATE_TREE_URL}?include_prior=true&max_depth=1",
            json=SAMPLE_TREE_RESPONSE_TRUNCATED,
        )

        resp = await fetch_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            include_prior=True,
            max_depth=1,
        )

        assert resp.truncation is not None
        assert resp.truncation.truncated_company_ids == [SNL, IHS_MARKIT, NJ_DATA_CENTER]


class TestFetchUltimateParentPaths:
    @pytest.mark.asyncio
    async def test_fetch_ultimate_parent_paths(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """WHEN we fetch ultimate parent paths THEN each path runs company-first, parent-last."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/corporate_tree/{MCGRAW_HILL_EDUCATION}/ultimate_parent_paths",
            json=MULTI_PATHS_RESPONSE,
        )

        resp = await fetch_ultimate_parent_paths(
            company_id=MCGRAW_HILL_EDUCATION,
            httpx_client=httpx_client,
        )

        assert len(resp.paths) == 2
        for path in resp.paths:
            assert path[0].company_id == MCGRAW_HILL_EDUCATION
            assert path[-1].company_id == SPGI_COMPANY_ID
            # The ultimate parent terminates the path, so it has no parent and no relationship.
            assert path[-1].parent_company_id is None
            assert path[-1].relationship_type is None
        # The two chains diverge above The McGraw-Hill Companies.
        assert resp.paths[0][1].parent_company_id == SNL
        assert resp.paths[1][1].parent_company_id == NJ_DATA_CENTER


# --- Tests for get_ultimate_parent_paths ---


class TestGetUltimateParentPaths:
    @pytest.mark.asyncio
    async def test_get_ultimate_parent_paths_from_identifiers(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """WHEN the tool is called THEN identifiers resolve and the wire model is returned."""
        httpx_mock.add_response(
            method="GET", url=ULTIMATE_PARENT_PATHS_URL, json=MULTI_PATHS_RESPONSE
        )

        resp = await get_ultimate_parent_paths_from_identifiers(
            identifiers=["SPGI"], httpx_client=httpx_client
        )

        assert resp.errors == []
        assert resp.identifier_info == {"SPGI": SPGI_ID_TRIPLE}
        assert len(resp.identifier_results["SPGI"].paths) == 2

    @pytest.mark.asyncio
    async def test_get_ultimate_parent_paths_for_company_with_no_parent(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """WHEN a company has no controlling parent THEN a single one-element path is returned."""
        httpx_mock.add_response(
            method="GET", url=ULTIMATE_PARENT_PATHS_URL, json=SINGLE_PATH_RESPONSE
        )

        resp = await get_ultimate_parent_paths_from_identifiers(
            identifiers=["SPGI"], httpx_client=httpx_client
        )

        paths = resp.identifier_results["SPGI"].paths
        assert len(paths) == 1
        assert len(paths[0]) == 1
        assert paths[0][0].company_id == SPGI_COMPANY_ID
        assert paths[0][0].parent_company_id is None
        assert paths[0][0].relationship_type is None

    @pytest.mark.asyncio
    async def test_get_ultimate_parent_paths_with_unresolvable_identifier(
        self, httpx_client: httpx.AsyncClient
    ) -> None:
        """WHEN an identifier cannot be resolved THEN the error is reported and no call is made."""
        resp = await get_ultimate_parent_paths_from_identifiers(
            identifiers=["non-existent"], httpx_client=httpx_client
        )

        assert resp.identifier_results == {}
        assert len(resp.errors) == 1


# --- Tests for search_corporate_tree ---


class TestSearchCorporateTree:
    @pytest.fixture
    def add_tree_mock(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{CORPORATE_TREE_URL}?include_prior=false",
            json=SAMPLE_TREE_RESPONSE,
            is_optional=True,
            is_reusable=True,
        )

    @pytest.mark.asyncio
    async def test_search_without_filters_returns_every_edge(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN no filters are given THEN every relationship is returned, one row per edge."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID, httpx_client=httpx_client
        )

        assert result.root.company_id == SPGI_COMPANY_ID
        assert result.summary.total_matches == 12
        assert result.summary.distinct_companies == 8
        assert result.summary.showing == 12
        assert len(result.nodes) == 12
        assert result.summary.matches_by_level == {"1": 4, "2": 6, "3": 2}
        assert result.summary.tree_total_companies == 9
        assert result.summary.tree_total_edges == 12
        assert result.summary.tree_max_depth == 3
        assert result.summary.truncated_company_ids == []

    @pytest.mark.asyncio
    async def test_search_never_matches_the_root(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN the filter matches only the queried company THEN there are no matches."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID, httpx_client=httpx_client, name=["S&P Global"]
        )

        assert result.summary.total_matches == 0
        assert result.nodes == []
        assert result.summary.matches_by_level == {}
        # The root is still reported so the caller knows whose tree was searched.
        assert result.root.company_name == "S&P Global Inc."

    @pytest.mark.asyncio
    async def test_search_by_relationship_type(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN relationship_type is given THEN only edges of that type match."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            relationship_type=[TreeRelationshipType.merged_entity],
        )

        assert result.summary.total_matches == 2
        assert {node.company_id for node in result.nodes} == {NJ_DATA_CENTER, KENSHO}
        assert all(
            node.relationship_type is TreeRelationshipType.merged_entity for node in result.nodes
        )

    @pytest.mark.asyncio
    async def test_search_by_multiple_relationship_types(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN several relationship types are given THEN edges matching ANY of them match."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            relationship_type=[
                TreeRelationshipType.merged_entity,
                TreeRelationshipType.investment_arm,
            ],
        )

        assert result.summary.total_matches == 3
        assert {node.company_id for node in result.nodes} == {NJ_DATA_CENTER, KENSHO, OSTTRA}

    @pytest.mark.asyncio
    @pytest.mark.parametrize("country_iso_code", ["GBR", "gbr"])
    async def test_search_by_country_iso_code_is_case_insensitive(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None, country_iso_code: str
    ) -> None:
        """WHEN an ISO alpha-3 code is given in any case THEN the same edges match."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            country_iso_code=[country_iso_code],
        )

        # IHS Markit is reached at level 1 and again at level 3, so 3 edges over 2 companies.
        assert result.summary.total_matches == 3
        assert result.summary.distinct_companies == 2
        assert {node.company_id for node in result.nodes} == {IHS_MARKIT, OSTTRA}

    @pytest.mark.asyncio
    @pytest.mark.parametrize("country_iso_code", ["United Kingdom", "GB", "UK"])
    async def test_search_by_country_iso_code_ignores_full_names_and_other_codes(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None, country_iso_code: str
    ) -> None:
        """WHEN anything but an alpha-3 code is given THEN it matches nothing."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            country_iso_code=[country_iso_code],
        )

        assert result.summary.total_matches == 0
        assert result.nodes == []

    @pytest.mark.asyncio
    async def test_search_by_country_iso_code_excludes_companies_with_no_country(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """WHEN a company has no iso_country THEN a country_iso_code filter never matches it."""
        httpx_mock.add_response(
            method="GET",
            url=f"{CORPORATE_TREE_URL}?include_prior=false",
            json=SAMPLE_TREE_RESPONSE_NO_COUNTRY,
            is_reusable=True,
        )

        filtered = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID, httpx_client=httpx_client, country_iso_code=["USA"]
        )
        assert filtered.summary.total_matches == 0

        # Without the filter the same company is still returned.
        unfiltered = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID, httpx_client=httpx_client
        )
        assert unfiltered.summary.total_matches == 1
        assert unfiltered.nodes[0].iso_country is None

    @pytest.mark.asyncio
    async def test_search_by_multiple_country_iso_codes(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN several countries are given THEN edges in ANY of them match."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID, httpx_client=httpx_client, country_iso_code=["GBR", "USA"]
        )

        assert result.summary.total_matches == 12

    @pytest.mark.asyncio
    async def test_search_by_name_substring(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN a name substring is given THEN it matches company names case-insensitively."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID, httpx_client=httpx_client, name=["mcgraw"]
        )

        assert result.summary.distinct_companies == 3
        assert {node.company_id for node in result.nodes} == {
            NJ_DATA_CENTER,
            JUVENILE_RETAIL,
            MCGRAW_HILL_EDUCATION,
        }

    @pytest.mark.asyncio
    async def test_search_by_multiple_names(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN several name substrings are given THEN companies matching ANY of them match."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID, httpx_client=httpx_client, name=["Kensho", "Osttra"]
        )

        assert {node.company_id for node in result.nodes} == {KENSHO, OSTTRA}

    @pytest.mark.asyncio
    async def test_search_combines_filters_with_and_logic(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN several filter types are given THEN a node must satisfy all of them."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            country_iso_code=["GBR"],
            relationship_type=[TreeRelationshipType.subsidiary_or_operating_unit],
        )

        # Osttra is in GBR but is an investment arm, so only the two IHS Markit edges match.
        assert result.summary.total_matches == 2
        assert result.summary.distinct_companies == 1
        assert {node.company_id for node in result.nodes} == {IHS_MARKIT}

    @pytest.mark.asyncio
    async def test_search_with_contradictory_filters_returns_nothing(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN filters cannot be satisfied together THEN no nodes are returned."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            country_iso_code=["USA"],
            relationship_type=[TreeRelationshipType.investment_arm],
        )

        assert result.summary.total_matches == 0
        assert result.nodes == []

    @pytest.mark.asyncio
    async def test_search_reports_a_company_once_per_parent(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN a company has several parents THEN it is returned once per parent."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID, httpx_client=httpx_client, name=["Juvenile Retail"]
        )

        assert result.summary.total_matches == 2
        assert result.summary.distinct_companies == 1
        assert {node.parent_company_id for node in result.nodes} == {SNL, NJ_DATA_CENTER}

    @pytest.mark.asyncio
    async def test_search_limit_truncates_nodes_but_not_the_totals(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN limit is below the match count THEN nodes are capped but total_matches is not."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID, httpx_client=httpx_client, limit=3
        )

        assert result.summary.total_matches == 12
        assert result.summary.showing == 3
        assert len(result.nodes) == 3
        # matches_by_level describes every match, not just the ones shown.
        assert sum(result.summary.matches_by_level.values()) == 12

    @pytest.mark.asyncio
    async def test_search_flattens_node_fields(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN a node is returned THEN the nested company fields are flattened onto it."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID, httpx_client=httpx_client, name=["Osttra"]
        )

        (node,) = result.nodes
        assert node.company_id == OSTTRA
        assert node.company_name == "Osttra Group Ltd."
        assert node.country == "United Kingdom"
        assert node.iso_country == "GBR"
        assert node.parent_company_id == IHS_MARKIT
        assert node.level == 2
        assert node.relationship_type is TreeRelationshipType.investment_arm

    @pytest.mark.asyncio
    async def test_search_sends_max_depth_and_include_prior(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """WHEN max_depth and include_prior are given THEN both reach the request URL."""
        httpx_mock.add_response(
            method="GET",
            url=f"{CORPORATE_TREE_URL}?include_prior=true&max_depth=1",
            json=SAMPLE_TREE_RESPONSE_TRUNCATED,
        )

        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            max_depth=1,
            include_prior=True,
        )

        assert result.summary.total_matches == 4
        assert result.summary.matches_by_level == {"1": 4}
        assert result.summary.truncated_company_ids == [SNL, IHS_MARKIT, NJ_DATA_CENTER]

    @pytest.mark.asyncio
    async def test_search_orders_level_keys_numerically(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """WHEN a tree is deeper than 9 levels THEN level keys are ordered numerically."""
        httpx_mock.add_response(
            method="GET",
            url=f"{CORPORATE_TREE_URL}?include_prior=false",
            json=SAMPLE_DEEP_TREE_RESPONSE,
        )

        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID, httpx_client=httpx_client
        )

        assert list(result.summary.matches_by_level) == [str(level) for level in range(1, 11)]

    @pytest.mark.asyncio
    async def test_search_corporate_tree_from_identifiers(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN the full tool function is called THEN identifiers resolve and trees are searched."""
        resp = await search_corporate_tree_from_identifiers(
            identifiers=["SPGI"], httpx_client=httpx_client, country_iso_code=["GBR"]
        )

        assert resp.errors == []
        assert resp.identifier_info == {"SPGI": SPGI_ID_TRIPLE}
        assert resp.identifier_results["SPGI"].summary.distinct_companies == 2

    @pytest.mark.asyncio
    async def test_search_corporate_tree_with_unresolvable_identifier(
        self, httpx_client: httpx.AsyncClient
    ) -> None:
        """WHEN an identifier cannot be resolved THEN the error is reported and no call is made."""
        resp = await search_corporate_tree_from_identifiers(
            identifiers=["non-existent"], httpx_client=httpx_client
        )

        assert resp.identifier_results == {}
        assert len(resp.errors) == 1
