import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.conftest import SPGI_COMPANY_ID, SPGI_ID_TRIPLE
from kfinance.domains.corporate_tree.corporate_tree_models import TreeRelationshipType
from kfinance.domains.corporate_tree.corporate_tree_tools import (
    CorporateTreeSearchResult,
    CorporateTreeSummaryResult,
    UltimateParentPathResult,
    fetch_and_search_corporate_tree,
    fetch_and_summarize_corporate_tree,
    fetch_corporate_tree,
    fetch_ultimate_parent_path,
    get_corporate_tree_summary_from_identifiers,
    get_ultimate_parent_path_from_identifiers,
    search_corporate_tree_from_identifiers,
)


# --- Test fixtures ---

SAMPLE_TREE_RESPONSE = {
    "root": {
        "company": {"id": SPGI_COMPANY_ID, "name": "S&P Global Inc.", "country": "United States", "iso_country": "USA"},
        "children": [
            {
                "company": {"id": 100, "name": "S&P Global Market Intelligence", "country": "United States", "iso_country": "USA"},
                "relationship_type": "SUBSIDIARY_OR_OPERATING_UNIT",
                "relationship_status": "CURRENT",
                "controlling_interest": True,
                "children": [
                    {
                        "company": {"id": 101, "name": "Capital IQ", "country": "United States", "iso_country": "USA"},
                        "relationship_type": "SUBSIDIARY_OR_OPERATING_UNIT",
                        "relationship_status": "CURRENT",
                        "controlling_interest": True,
                        "children": [],
                    },
                    {
                        "company": {"id": 102, "name": "S&P Global UK Ltd", "country": "United Kingdom", "iso_country": "GBR"},
                        "relationship_type": "SUBSIDIARY_OR_OPERATING_UNIT",
                        "relationship_status": "CURRENT",
                        "controlling_interest": True,
                        "children": [],
                    },
                ],
            },
            {
                "company": {"id": 200, "name": "S&P Global Ratings", "country": "United States", "iso_country": "USA"},
                "relationship_type": "SUBSIDIARY_OR_OPERATING_UNIT",
                "relationship_status": "CURRENT",
                "controlling_interest": True,
                "children": [],
            },
            {
                "company": {"id": 300, "name": "CRISIL Limited", "country": "India", "iso_country": "IND"},
                "relationship_type": "AFFILIATE",
                "relationship_status": "CURRENT",
                "controlling_interest": False,
                "children": [],
            },
            {
                "company": {"id": 400, "name": "Old Subsidiary Inc.", "country": "United States", "iso_country": "USA"},
                "relationship_type": "MERGED_ENTITY",
                "relationship_status": "PRIOR",
                "controlling_interest": True,
                "children": [],
            },
        ],
    },
    "truncation": None,
    "ultimate_parent_path": [
        {"id": 50000, "name": "Ultimate Parent Corp", "country": "United States", "iso_country": "USA"},
        {"id": SPGI_COMPANY_ID, "name": "S&P Global Inc.", "country": "United States", "iso_country": "USA"},
    ],
}

SAMPLE_TREE_RESPONSE_NO_PARENT = {
    "root": {
        "company": {"id": SPGI_COMPANY_ID, "name": "S&P Global Inc.", "country": "United States", "iso_country": "USA"},
        "children": [],
    },
    "truncation": None,
    "ultimate_parent_path": None,
}

SAMPLE_TREE_RESPONSE_TRUNCATED = {
    "root": {
        "company": {"id": SPGI_COMPANY_ID, "name": "S&P Global Inc.", "country": "United States", "iso_country": "USA"},
        "children": [
            {
                "company": {"id": 100, "name": "Sub A", "country": "United States", "iso_country": "USA"},
                "relationship_type": "SUBSIDIARY_OR_OPERATING_UNIT",
                "relationship_status": "CURRENT",
                "controlling_interest": True,
                "children": [],
            },
        ],
    },
    "truncation": {"max_nodes": 2000, "returned_nodes": 2000, "max_level_reached": 5},
    "ultimate_parent_path": None,
}

CORPORATE_TREE_URL = f"https://kfinance.kensho.com/api/v1/corporate_tree/{SPGI_COMPANY_ID}"


# A simple mock kfinance_api_client (only used for constructing CorporateTree objects, not for I/O)
class MockKfinanceApiClient:
    pass


MOCK_API_CLIENT = MockKfinanceApiClient()


# --- Tests for fetch_corporate_tree ---


class TestFetchCorporateTree:
    @pytest.mark.asyncio
    async def test_fetch_corporate_tree(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """WHEN we fetch a corporate tree THEN we get a valid CorporateTreeResponse."""
        httpx_mock.add_response(
            method="GET",
            url=f"{CORPORATE_TREE_URL}?include_prior=false&include_ultimate_parent_path=true&max_depth=1",
            json=SAMPLE_TREE_RESPONSE,
        )

        resp = await fetch_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            include_ultimate_parent_path=True,
            max_depth=1,
        )

        assert resp.root.company.id == SPGI_COMPANY_ID
        assert resp.ultimate_parent_path is not None
        assert len(resp.ultimate_parent_path) == 2

    @pytest.mark.asyncio
    async def test_fetch_corporate_tree_with_include_prior(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """WHEN we fetch with include_prior=True THEN the URL includes include_prior=true."""
        httpx_mock.add_response(
            method="GET",
            url=f"{CORPORATE_TREE_URL}?include_prior=true&include_ultimate_parent_path=false&max_depth=20",
            json=SAMPLE_TREE_RESPONSE,
        )

        resp = await fetch_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            include_prior=True,
            max_depth=20,
        )

        assert resp.root.company.id == SPGI_COMPANY_ID


# --- Tests for get_ultimate_parent_path ---


class TestGetUltimateParentPath:
    @pytest.fixture
    def add_tree_mock(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{CORPORATE_TREE_URL}?include_prior=false&include_ultimate_parent_path=true&max_depth=0",
            json=SAMPLE_TREE_RESPONSE,
            is_optional=True,
            is_reusable=True,
        )

    @pytest.fixture
    def add_tree_no_parent_mock(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{CORPORATE_TREE_URL}?include_prior=false&include_ultimate_parent_path=true&max_depth=0",
            json=SAMPLE_TREE_RESPONSE_NO_PARENT,
            is_optional=True,
            is_reusable=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_ultimate_parent_path(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN a company has an ultimate parent THEN the path is returned."""
        result = await fetch_ultimate_parent_path(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
        )

        assert len(result.path) == 2
        assert result.path[0].id == 50000
        assert result.path[0].name == "Ultimate Parent Corp"
        assert result.path[1].id == SPGI_COMPANY_ID

    @pytest.mark.asyncio
    async def test_fetch_ultimate_parent_path_is_ultimate_parent(
        self, httpx_client: httpx.AsyncClient, add_tree_no_parent_mock: None
    ) -> None:
        """WHEN a company is its own ultimate parent THEN path contains only itself."""
        result = await fetch_ultimate_parent_path(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
        )

        assert len(result.path) == 1
        assert result.path[0].id == SPGI_COMPANY_ID

    @pytest.mark.asyncio
    async def test_get_ultimate_parent_path_from_identifiers(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN we call the full tool function THEN it resolves identifiers and returns paths."""
        resp = await get_ultimate_parent_path_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
        )

        assert "SPGI" in resp.identifier_results
        assert resp.identifier_results["SPGI"].path[0].name == "Ultimate Parent Corp"
        assert len(resp.errors) == 0

    @pytest.mark.asyncio
    async def test_get_ultimate_parent_path_with_error(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN an identifier can't be resolved THEN errors are returned."""
        resp = await get_ultimate_parent_path_from_identifiers(
            identifiers=["non-existent"],
            httpx_client=httpx_client,
        )

        assert len(resp.identifier_results) == 0
        assert len(resp.errors) == 1


# --- Tests for search_corporate_tree ---


class TestSearchCorporateTree:
    @pytest.fixture
    def add_tree_mock(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{CORPORATE_TREE_URL}?include_prior=false&include_ultimate_parent_path=false&max_depth=20",
            json=SAMPLE_TREE_RESPONSE,
            is_optional=True,
            is_reusable=True,
        )

    @pytest.fixture
    def add_tree_depth_1_mock(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{CORPORATE_TREE_URL}?include_prior=false&include_ultimate_parent_path=false&max_depth=1",
            json=SAMPLE_TREE_RESPONSE,
            is_optional=True,
            is_reusable=True,
        )

    @pytest.fixture
    def add_tree_with_prior_mock(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{CORPORATE_TREE_URL}?include_prior=true&include_ultimate_parent_path=false&max_depth=20",
            json=SAMPLE_TREE_RESPONSE,
            is_optional=True,
            is_reusable=True,
        )

    @pytest.mark.asyncio
    async def test_search_no_filter(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN no filters are specified THEN all nodes (up to limit) are returned."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            kfinance_api_client=MOCK_API_CLIENT,
        )

        # Root is at depth 0 and gets searched; 4 direct children + 2 grandchildren + root = 7
        # But search starts at root node (depth=0), and root has no relationship_type
        # so all 7 nodes are traversed
        assert len(result.nodes) > 0
        assert result.is_truncated is False

    @pytest.mark.asyncio
    async def test_search_by_relationship_type(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN filtering by relationship_type THEN only matching nodes are returned."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            kfinance_api_client=MOCK_API_CLIENT,
            relationship_type=TreeRelationshipType.affiliate,
        )

        assert len(result.nodes) == 1
        assert result.nodes[0].company_name == "CRISIL Limited"
        assert result.nodes[0].relationship_type == "AFFILIATE"
        assert result.nodes[0].level == 1

    @pytest.mark.asyncio
    async def test_search_by_country(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN filtering by country THEN only nodes in that country are returned."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            kfinance_api_client=MOCK_API_CLIENT,
            country="GBR",
        )

        assert len(result.nodes) == 1
        assert result.nodes[0].company_name == "S&P Global UK Ltd"
        assert result.nodes[0].level == 2  # grandchild

    @pytest.mark.asyncio
    async def test_search_by_name(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN filtering by name substring THEN matching nodes are returned."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            kfinance_api_client=MOCK_API_CLIENT,
            name="Capital",
        )

        assert len(result.nodes) == 1
        assert result.nodes[0].company_name == "Capital IQ"
        assert result.nodes[0].level == 2  # grandchild

    @pytest.mark.asyncio
    async def test_search_direct_children_only(
        self, httpx_client: httpx.AsyncClient, add_tree_depth_1_mock: None
    ) -> None:
        """WHEN direct_children_only=True THEN only direct children are searched."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            kfinance_api_client=MOCK_API_CLIENT,
            direct_children_only=True,
            relationship_type=TreeRelationshipType.subsidiary_or_operating_unit,
        )

        # Direct children that are subsidiaries: "S&P Global Market Intelligence" and "S&P Global Ratings"
        # "Capital IQ" and "S&P Global UK Ltd" are grandchildren (depth 2), excluded by max_depth=1
        names = [n.company_name for n in result.nodes]
        assert "S&P Global Market Intelligence" in names
        assert "S&P Global Ratings" in names
        assert "Capital IQ" not in names

    @pytest.mark.asyncio
    async def test_search_combined_filters(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN multiple filters are combined THEN AND logic is applied."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            kfinance_api_client=MOCK_API_CLIENT,
            relationship_type=TreeRelationshipType.subsidiary_or_operating_unit,
            country="USA",
        )

        # All US subsidiaries (not affiliates, not UK)
        names = [n.company_name for n in result.nodes]
        assert "S&P Global Market Intelligence" in names
        assert "Capital IQ" in names
        assert "S&P Global Ratings" in names
        assert "CRISIL Limited" not in names  # affiliate, not subsidiary
        assert "S&P Global UK Ltd" not in names  # GBR, not USA

    @pytest.mark.asyncio
    async def test_search_with_include_prior(
        self, httpx_client: httpx.AsyncClient, add_tree_with_prior_mock: None
    ) -> None:
        """WHEN include_prior=True THEN the fetch uses include_prior=true."""
        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            kfinance_api_client=MOCK_API_CLIENT,
            include_prior=True,
            relationship_type=TreeRelationshipType.merged_entity,
        )

        assert len(result.nodes) == 1
        assert result.nodes[0].company_name == "Old Subsidiary Inc."

    @pytest.mark.asyncio
    async def test_search_truncated_tree(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """WHEN the tree is truncated THEN is_truncated=True in the response."""
        httpx_mock.add_response(
            method="GET",
            url=f"{CORPORATE_TREE_URL}?include_prior=false&include_ultimate_parent_path=false&max_depth=20",
            json=SAMPLE_TREE_RESPONSE_TRUNCATED,
        )

        result = await fetch_and_search_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            kfinance_api_client=MOCK_API_CLIENT,
        )

        assert result.is_truncated is True

    @pytest.mark.asyncio
    async def test_search_corporate_tree_from_identifiers(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN the full tool function is called THEN identifiers are resolved and trees searched."""
        resp = await search_corporate_tree_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            kfinance_api_client=MOCK_API_CLIENT,
            country="IND",
        )

        assert "SPGI" in resp.identifier_results
        result = resp.identifier_results["SPGI"]
        assert len(result.nodes) == 1
        assert result.nodes[0].company_name == "CRISIL Limited"


# --- Tests for get_corporate_tree_summary ---


class TestGetCorporateTreeSummary:
    @pytest.fixture
    def add_tree_mock(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{CORPORATE_TREE_URL}?include_prior=false&include_ultimate_parent_path=false&max_depth=20",
            json=SAMPLE_TREE_RESPONSE,
            is_optional=True,
            is_reusable=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_and_summarize(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN we summarize a corporate tree THEN correct stats are computed."""
        result = await fetch_and_summarize_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            kfinance_api_client=MOCK_API_CLIENT,
        )

        # Tree structure:
        # Level 0: root (1 node)
        # Level 1: Market Intelligence, Ratings, CRISIL, Old Subsidiary (4 nodes)
        # Level 2: Capital IQ, UK Ltd (2 nodes)
        # Total: 7 nodes
        assert result.total_nodes == 7
        assert result.nodes_per_level == {0: 1, 1: 4, 2: 2}
        assert result.nodes_per_type["SUBSIDIARY_OR_OPERATING_UNIT"] == 4
        assert result.nodes_per_type["AFFILIATE"] == 1
        assert result.nodes_per_type["MERGED_ENTITY"] == 1
        assert result.nodes_per_country["USA"] == 5
        assert result.nodes_per_country["GBR"] == 1
        assert result.nodes_per_country["IND"] == 1
        assert result.is_truncated is False

    @pytest.mark.asyncio
    async def test_summarize_truncated_tree(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """WHEN a tree is truncated THEN summary reports is_truncated=True."""
        httpx_mock.add_response(
            method="GET",
            url=f"{CORPORATE_TREE_URL}?include_prior=false&include_ultimate_parent_path=false&max_depth=20",
            json=SAMPLE_TREE_RESPONSE_TRUNCATED,
        )

        result = await fetch_and_summarize_corporate_tree(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            kfinance_api_client=MOCK_API_CLIENT,
        )

        assert result.is_truncated is True
        assert result.total_nodes == 2  # root + 1 child

    @pytest.mark.asyncio
    async def test_get_corporate_tree_summary_from_identifiers(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN the full tool function is called THEN identifiers are resolved and summaries returned."""
        resp = await get_corporate_tree_summary_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            kfinance_api_client=MOCK_API_CLIENT,
        )

        assert "SPGI" in resp.identifier_results
        result = resp.identifier_results["SPGI"]
        assert result.total_nodes == 7
        assert len(resp.errors) == 0

    @pytest.mark.asyncio
    async def test_get_summary_with_error(
        self, httpx_client: httpx.AsyncClient, add_tree_mock: None
    ) -> None:
        """WHEN an identifier can't be resolved THEN errors are returned."""
        resp = await get_corporate_tree_summary_from_identifiers(
            identifiers=["non-existent"],
            httpx_client=httpx_client,
            kfinance_api_client=MOCK_API_CLIENT,
        )

        assert len(resp.identifier_results) == 0
        assert len(resp.errors) == 1
