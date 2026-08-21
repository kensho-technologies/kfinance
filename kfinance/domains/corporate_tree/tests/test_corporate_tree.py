from datetime import datetime
from unittest import TestCase

from requests_mock import Mocker

from kfinance.client.fetch import KFinanceApiClient
from kfinance.client.kfinance import (
    Company,
    CorporateTree,
    CorporateTreeNode,
    CorporateTreeSummary,
)
from kfinance.domains.corporate_tree.corporate_tree_models import (
    CompanyInfo,
    CorporateTreeResponse,
    RootNode,
    TreeNode,
    TreeRelationshipStatus,
    TreeRelationshipType,
    TruncationInfo,
)


SAMPLE_CORPORATE_TREE_RESPONSE = {
    "root": {
        "company": {"id": 100, "name": "Parent Corp", "country": "United States", "iso_country": "USA"},
        "children": [
            {
                "company": {"id": 101, "name": "US Subsidiary", "country": "United States", "iso_country": "USA"},
                "relationship_type": "SUBSIDIARY_OR_OPERATING_UNIT",
                "relationship_status": "CURRENT",
                "controlling_interest": True,
                "children": [
                    {
                        "company": {"id": 103, "name": "US Grandchild", "country": "United States", "iso_country": "USA"},
                        "relationship_type": "SUBSIDIARY_OR_OPERATING_UNIT",
                        "relationship_status": "CURRENT",
                        "controlling_interest": True,
                        "children": [],
                    }
                ],
            },
            {
                "company": {"id": 102, "name": "UK Affiliate", "country": "United Kingdom", "iso_country": "GBR"},
                "relationship_type": "AFFILIATE",
                "relationship_status": "CURRENT",
                "controlling_interest": False,
                "children": [],
            },
            {
                "company": {"id": 104, "name": "DE Investment Arm", "country": "Germany", "iso_country": "DEU"},
                "relationship_type": "INVESTMENT_ARM",
                "relationship_status": "CURRENT",
                "controlling_interest": True,
                "children": [],
            },
            {
                "company": {"id": 105, "name": "Former Sub", "country": "United States", "iso_country": "USA"},
                "relationship_type": "SUBSIDIARY_OR_OPERATING_UNIT",
                "relationship_status": "PRIOR",
                "controlling_interest": False,
                "children": [],
            },
        ],
    },
    "truncation": None,
    "ultimate_parent_path": [
        {"id": 99, "name": "Ultimate Parent Inc", "country": "United States", "iso_country": "USA"},
        {"id": 100, "name": "Parent Corp", "country": "United States", "iso_country": "USA"},
    ],
}

SAMPLE_TRUNCATED_RESPONSE = {
    "root": {
        "company": {"id": 100, "name": "Parent Corp", "country": "United States", "iso_country": "USA"},
        "children": [
            {
                "company": {"id": 101, "name": "Child 1", "country": "United States", "iso_country": "USA"},
                "relationship_type": "SUBSIDIARY_OR_OPERATING_UNIT",
                "relationship_status": "CURRENT",
                "controlling_interest": True,
                "children": [],
            },
        ],
    },
    "truncation": {
        "max_nodes": 2000,
        "returned_nodes": 2000,
        "max_level_reached": 15,
    },
    "ultimate_parent_path": [
        {"id": 100, "name": "Parent Corp", "country": "United States", "iso_country": "USA"},
    ],
}


class TestCorporateTreeModels(TestCase):
    """Test Pydantic model validation for corporate tree response."""

    def test_model_validates_full_response(self) -> None:
        response = CorporateTreeResponse.model_validate(SAMPLE_CORPORATE_TREE_RESPONSE)
        assert response.root.company.id == 100
        assert response.root.company.name == "Parent Corp"
        assert len(response.root.children) == 4
        assert response.truncation is None
        assert response.ultimate_parent_path is not None
        assert len(response.ultimate_parent_path) == 2

    def test_model_validates_truncated_response(self) -> None:
        response = CorporateTreeResponse.model_validate(SAMPLE_TRUNCATED_RESPONSE)
        assert response.truncation is not None
        assert response.truncation.max_nodes == 2000
        assert response.truncation.returned_nodes == 2000
        assert response.truncation.max_level_reached == 15

    def test_recursive_children(self) -> None:
        response = CorporateTreeResponse.model_validate(SAMPLE_CORPORATE_TREE_RESPONSE)
        first_child = response.root.children[0]
        assert first_child.company.name == "US Subsidiary"
        assert len(first_child.children) == 1
        grandchild = first_child.children[0]
        assert grandchild.company.name == "US Grandchild"
        assert grandchild.relationship_type == TreeRelationshipType.subsidiary_or_operating_unit

    def test_relationship_types(self) -> None:
        response = CorporateTreeResponse.model_validate(SAMPLE_CORPORATE_TREE_RESPONSE)
        children = response.root.children
        assert children[0].relationship_type == TreeRelationshipType.subsidiary_or_operating_unit
        assert children[1].relationship_type == TreeRelationshipType.affiliate
        assert children[2].relationship_type == TreeRelationshipType.investment_arm

    def test_relationship_statuses(self) -> None:
        response = CorporateTreeResponse.model_validate(SAMPLE_CORPORATE_TREE_RESPONSE)
        children = response.root.children
        assert children[0].relationship_status == TreeRelationshipStatus.current
        assert children[3].relationship_status == TreeRelationshipStatus.prior

    def test_response_without_ultimate_parent_path(self) -> None:
        data = {
            "root": {
                "company": {"id": 100, "name": "Root", "country": None, "iso_country": None},
                "children": [],
            },
        }
        response = CorporateTreeResponse.model_validate(data)
        assert response.ultimate_parent_path is None
        assert response.truncation is None


def _make_api_client() -> KFinanceApiClient:
    """Create a KFinanceApiClient with fake auth for testing."""
    client = KFinanceApiClient(refresh_token="fake")
    client._access_token = "fake"  # noqa: SLF001
    client._access_token_expiry = int(datetime(2100, 1, 1).timestamp())  # noqa: SLF001
    return client


class TestFetchCorporateTree(TestCase):
    """Test the fetch_corporate_tree method of KFinanceApiClient."""

    def test_fetch_corporate_tree_default_params(self) -> None:
        with Mocker() as m:
            m.get(
                url="https://kfinance.kensho.com/api/v1/corporate_tree/100"
                "?include_prior=false&include_ultimate_parent_path=true&max_depth=20",
                json=SAMPLE_CORPORATE_TREE_RESPONSE,
            )
            client = _make_api_client()
            response = client.fetch_corporate_tree(company_id=100)

        assert isinstance(response, CorporateTreeResponse)
        assert response.root.company.id == 100

    def test_fetch_corporate_tree_with_params(self) -> None:
        with Mocker() as m:
            m.get(
                url="https://kfinance.kensho.com/api/v1/corporate_tree/100"
                "?include_prior=true&include_ultimate_parent_path=false&max_depth=5",
                json=SAMPLE_CORPORATE_TREE_RESPONSE,
            )
            client = _make_api_client()
            response = client.fetch_corporate_tree(
                company_id=100,
                include_prior=True,
                include_ultimate_parent_path=False,
                max_depth=5,
            )

        assert isinstance(response, CorporateTreeResponse)


def _build_corporate_tree(response_data: dict) -> CorporateTree:
    """Helper to build a CorporateTree from raw response data using a mock API client."""
    client = _make_api_client()
    response = CorporateTreeResponse.model_validate(response_data)

    def _build_node(tree_node: TreeNode) -> CorporateTreeNode:
        return CorporateTreeNode(
            kfinance_api_client=client,
            company_info=tree_node.company,
            relationship_type=tree_node.relationship_type,
            relationship_status=tree_node.relationship_status,
            controlling_interest=tree_node.controlling_interest,
            children=[_build_node(child) for child in tree_node.children],
        )

    root_node = CorporateTreeNode(
        kfinance_api_client=client,
        company_info=response.root.company,
        relationship_type=None,
        relationship_status=None,
        controlling_interest=None,
        children=[_build_node(child) for child in response.root.children],
    )

    return CorporateTree(
        kfinance_api_client=client,
        root_node=root_node,
        ultimate_parent_path=response.ultimate_parent_path,
        truncation=response.truncation,
    )


class TestCorporateTreeNavigation(TestCase):
    """Test CorporateTree parent/ultimate parent navigation."""

    def test_parent_returns_company(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        parent = tree.parent
        assert parent is not None
        assert isinstance(parent, Company)
        assert parent.company_id == 99
        assert parent._company_name == "Ultimate Parent Inc"

    def test_parent_returns_none_when_is_ultimate_parent(self) -> None:
        tree = _build_corporate_tree(SAMPLE_TRUNCATED_RESPONSE)
        # ultimate_parent_path has only one element (the company itself)
        assert tree.parent is None

    def test_ultimate_parent_returns_company(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        ult = tree.ultimate_parent
        assert isinstance(ult, Company)
        assert ult.company_id == 99
        assert ult._company_name == "Ultimate Parent Inc"

    def test_ultimate_parent_fallback_to_root(self) -> None:
        data = {
            "root": {
                "company": {"id": 100, "name": "Root Co", "country": None, "iso_country": None},
                "children": [],
            },
        }
        tree = _build_corporate_tree(data)
        ult = tree.ultimate_parent
        assert isinstance(ult, Company)
        assert ult.company_id == 100

    def test_ultimate_parent_path_returns_list_of_companies(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        path = tree.ultimate_parent_path
        assert path is not None
        assert len(path) == 2
        assert all(isinstance(c, Company) for c in path)
        assert path[0].company_id == 99
        assert path[1].company_id == 100

    def test_ultimate_parent_path_none_when_not_requested(self) -> None:
        data = {
            "root": {
                "company": {"id": 100, "name": "Root Co", "country": None, "iso_country": None},
                "children": [],
            },
        }
        tree = _build_corporate_tree(data)
        assert tree.ultimate_parent_path is None


class TestCorporateTreeChildren(TestCase):
    """Test CorporateTree children filtering."""

    def test_direct_children_unfiltered(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        assert len(tree.direct_children) == 4

    def test_children_no_filter(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        assert len(tree.children()) == 4

    def test_children_filter_by_relationship_type(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        subs = tree.children(relationship_type=TreeRelationshipType.subsidiary_or_operating_unit)
        assert len(subs) == 2  # US Subsidiary + Former Sub
        assert all(
            n.relationship_type == TreeRelationshipType.subsidiary_or_operating_unit for n in subs
        )

    def test_children_filter_by_country(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        usa_children = tree.children(country="USA")
        assert len(usa_children) == 2  # US Subsidiary + Former Sub (not GBR/DEU)

    def test_children_filter_by_country_case_insensitive(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        gbr_children = tree.children(country="gbr")
        assert len(gbr_children) == 1
        assert gbr_children[0].company_name == "UK Affiliate"

    def test_children_combined_filter(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        result = tree.children(
            relationship_type=TreeRelationshipType.subsidiary_or_operating_unit,
            country="USA",
        )
        assert len(result) == 2  # US Subsidiary + Former Sub

    def test_children_filter_no_matches(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        result = tree.children(country="JPN")
        assert len(result) == 0


class TestCorporateTreeSummary(TestCase):
    """Test CorporateTree summary statistics."""

    def test_summary_total_nodes(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        summary = tree.summary()
        # root + 4 children + 1 grandchild = 6
        assert summary.total_nodes == 6

    def test_summary_nodes_per_level(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        summary = tree.summary()
        assert summary.nodes_per_level == {0: 1, 1: 4, 2: 1}

    def test_summary_nodes_per_type(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        summary = tree.summary()
        # 3 SUBSIDIARY_OR_OPERATING_UNIT (US Sub, US Grandchild, Former Sub), 1 AFFILIATE, 1 INVESTMENT_ARM
        assert summary.nodes_per_type == {
            "SUBSIDIARY_OR_OPERATING_UNIT": 3,
            "AFFILIATE": 1,
            "INVESTMENT_ARM": 1,
        }

    def test_summary_nodes_per_country(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        summary = tree.summary()
        assert summary.nodes_per_country == {"USA": 4, "GBR": 1, "DEU": 1}

    def test_summary_is_truncated_false(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        summary = tree.summary()
        assert summary.is_truncated is False

    def test_summary_is_truncated_true(self) -> None:
        tree = _build_corporate_tree(SAMPLE_TRUNCATED_RESPONSE)
        summary = tree.summary()
        assert summary.is_truncated is True


class TestCorporateTreeTruncation(TestCase):
    """Test CorporateTree truncation detection."""

    def test_is_truncated_false(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        assert tree.is_truncated is False
        assert tree.truncation_info is None

    def test_is_truncated_true(self) -> None:
        tree = _build_corporate_tree(SAMPLE_TRUNCATED_RESPONSE)
        assert tree.is_truncated is True
        assert tree.truncation_info is not None
        assert tree.truncation_info.max_nodes == 2000
        assert tree.truncation_info.returned_nodes == 2000
        assert tree.truncation_info.max_level_reached == 15


class TestCorporateTreeNode(TestCase):
    """Test CorporateTreeNode properties and methods."""

    def test_node_properties(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        node = tree.direct_children[0]
        assert node.company_id == 101
        assert node.company_name == "US Subsidiary"
        assert node.country == "United States"
        assert node.iso_country == "USA"
        assert node.relationship_type == TreeRelationshipType.subsidiary_or_operating_unit
        assert node.relationship_status == TreeRelationshipStatus.current
        assert node.controlling_interest is True

    def test_root_node_has_none_relationship(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        root = tree.root
        assert root.relationship_type is None
        assert root.relationship_status is None
        assert root.controlling_interest is None

    def test_to_company(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        node = tree.direct_children[0]
        company = node.to_company()
        assert isinstance(company, Company)
        assert company.company_id == 101
        assert company._company_name == "US Subsidiary"

    def test_node_children(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        node = tree.direct_children[0]
        assert len(node.children) == 1
        assert node.children[0].company_name == "US Grandchild"

    def test_str_repr(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        node = tree.direct_children[0]
        assert "US Subsidiary" in str(node)
        assert "101" in str(node)


class TestCorporateTreeChaining(TestCase):
    """Test chaining support via get_corporate_tree."""

    def test_get_corporate_tree_via_company(self) -> None:
        """Test that Company.get_corporate_tree() works end-to-end with mocked API."""
        with Mocker() as m:
            m.get(
                url="https://kfinance.kensho.com/api/v1/corporate_tree/100"
                "?include_prior=false&include_ultimate_parent_path=true&max_depth=20",
                json=SAMPLE_CORPORATE_TREE_RESPONSE,
            )
            client = _make_api_client()
            company = Company(
                kfinance_api_client=client,
                company_id=100,
                company_name="Parent Corp",
            )
            tree = company.get_corporate_tree()

        assert isinstance(tree, CorporateTree)
        assert tree.root.company_id == 100
        assert len(tree.direct_children) == 4

    def test_chaining_ultimate_parent(self) -> None:
        """Test that tree.ultimate_parent returns a Company that can call get_corporate_tree."""
        ultimate_parent_response = {
            "root": {
                "company": {"id": 99, "name": "Ultimate Parent Inc", "country": "United States", "iso_country": "USA"},
                "children": [
                    {
                        "company": {"id": 100, "name": "Parent Corp", "country": "United States", "iso_country": "USA"},
                        "relationship_type": "SUBSIDIARY_OR_OPERATING_UNIT",
                        "relationship_status": "CURRENT",
                        "controlling_interest": True,
                        "children": [],
                    },
                ],
            },
            "truncation": None,
            "ultimate_parent_path": [
                {"id": 99, "name": "Ultimate Parent Inc", "country": "United States", "iso_country": "USA"},
            ],
        }

        with Mocker() as m:
            m.get(
                url="https://kfinance.kensho.com/api/v1/corporate_tree/100"
                "?include_prior=false&include_ultimate_parent_path=true&max_depth=20",
                json=SAMPLE_CORPORATE_TREE_RESPONSE,
            )
            m.get(
                url="https://kfinance.kensho.com/api/v1/corporate_tree/99"
                "?include_prior=false&include_ultimate_parent_path=true&max_depth=20",
                json=ultimate_parent_response,
            )
            client = _make_api_client()
            company = Company(kfinance_api_client=client, company_id=100)
            tree = company.get_corporate_tree()
            # Chain: get the tree for the ultimate parent
            parent_tree = tree.ultimate_parent.get_corporate_tree()

        assert parent_tree.root.company_id == 99
        assert parent_tree.root.company_name == "Ultimate Parent Inc"

    def test_chaining_child_node(self) -> None:
        """Test that node.to_company().get_corporate_tree() works."""
        child_response = {
            "root": {
                "company": {"id": 101, "name": "US Subsidiary", "country": "United States", "iso_country": "USA"},
                "children": [],
            },
            "truncation": None,
            "ultimate_parent_path": [
                {"id": 99, "name": "Ultimate Parent Inc", "country": "United States", "iso_country": "USA"},
                {"id": 100, "name": "Parent Corp", "country": "United States", "iso_country": "USA"},
                {"id": 101, "name": "US Subsidiary", "country": "United States", "iso_country": "USA"},
            ],
        }

        with Mocker() as m:
            m.get(
                url="https://kfinance.kensho.com/api/v1/corporate_tree/100"
                "?include_prior=false&include_ultimate_parent_path=true&max_depth=20",
                json=SAMPLE_CORPORATE_TREE_RESPONSE,
            )
            m.get(
                url="https://kfinance.kensho.com/api/v1/corporate_tree/101"
                "?include_prior=false&include_ultimate_parent_path=true&max_depth=20",
                json=child_response,
            )
            client = _make_api_client()
            company = Company(kfinance_api_client=client, company_id=100)
            tree = company.get_corporate_tree()
            # Chain: get the tree for the first child
            child_tree = tree.direct_children[0].to_company().get_corporate_tree()

        assert child_tree.root.company_id == 101
        # The child's parent should be Parent Corp (id=100)
        assert child_tree.parent is not None
        assert child_tree.parent.company_id == 100


class TestCorporateTreeStr(TestCase):
    """Test string representations."""

    def test_corporate_tree_str(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        s = str(tree)
        assert "Parent Corp" in s
        assert "total_nodes=6" in s
        assert "truncated=False" in s

    def test_corporate_tree_summary_str(self) -> None:
        tree = _build_corporate_tree(SAMPLE_CORPORATE_TREE_RESPONSE)
        summary = tree.summary()
        s = str(summary)
        assert "total_nodes=6" in s
        assert "is_truncated=False" in s
