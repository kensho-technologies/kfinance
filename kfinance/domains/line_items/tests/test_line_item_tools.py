import httpx
from langchain_core.utils.function_calling import convert_to_openai_tool
import pytest
from pytest_httpx import HTTPXMock

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX
from kfinance.domains.line_items.line_item_models import CalendarType, LineItemResp, LineItemScore
from kfinance.domains.line_items.line_item_tools import (
    GetFinancialLineItemFromIdentifiers,
    GetFinancialLineItemFromIdentifiersResp,
    _find_similar_line_items,
    fetch_line_item_from_company_ids,
    get_financial_line_item_from_identifiers,
)
from kfinance.domains.line_items.response_notes import (
    FISCAL_PERIOD_WARNING,
    FISCAL_YEAR_TERMINOLOGY_WARNING,
    SOURCE_LINK_NOTE,
)


class TestGetFinancialLineItemFromIdentifiers:
    line_item_resp = {
        "currency": "USD",
        "periods": {
            "CY2022": {
                "period_end_date": "2022-12-31",
                "num_months": 12,
                "line_item": {"name": "Revenue", "value": "11181000000.0", "sources": []},
            },
            "CY2023": {
                "period_end_date": "2023-12-31",
                "num_months": 12,
                "line_item": {"name": "Revenue", "value": "12497000000.0", "sources": []},
            },
            "CY2024": {
                "period_end_date": "2024-12-31",
                "num_months": 12,
                "line_item": {"name": "Revenue", "value": "14208000000.0", "sources": []},
            },
        },
    }

    @pytest.fixture
    def add_spgi_line_item_mock_resp(self, httpx_mock: HTTPXMock) -> None:
        """Add mock response for SPGI line items."""
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/line_item/",
            json={"results": {str(SPGI_ID_TRIPLE.company_id): self.line_item_resp}, "errors": {}},
            is_optional=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_line_item_from_company_ids(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_line_item_mock_resp: None,
    ) -> None:
        """
        WHEN we request SPGI's line items (using SPGI's company id)
        THEN we get back SPGI's line items
        """

        resp = await fetch_line_item_from_company_ids(
            company_ids=[SPGI_ID_TRIPLE.company_id],
            line_item="revenue",
            httpx_client=httpx_client,
        )

        expected_results = {
            str(SPGI_ID_TRIPLE.company_id): LineItemResp.model_validate(self.line_item_resp)
        }
        assert resp.results == expected_results
        assert resp.errors == {}

    @pytest.mark.parametrize(
        "calendar_type, expected_notes",
        [
            (CalendarType.calendar, [SOURCE_LINK_NOTE]),
            (
                CalendarType.fiscal,
                [SOURCE_LINK_NOTE, FISCAL_PERIOD_WARNING, FISCAL_YEAR_TERMINOLOGY_WARNING],
            ),
            (
                None,  # None defaults to fiscal
                [SOURCE_LINK_NOTE, FISCAL_PERIOD_WARNING, FISCAL_YEAR_TERMINOLOGY_WARNING],
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_financial_line_item_from_identifiers(
        self,
        calendar_type: CalendarType | None,
        expected_notes: list[str],
        httpx_client: httpx.AsyncClient,
        add_spgi_line_item_mock_resp: None,
    ) -> None:
        """
        WHEN we request revenue for SPGI and a non-existent company
        THEN we get back the SPGI revenue, an error for the non-existent company,
            and notes appropriate for the calendar type.
        """

        expected_response = GetFinancialLineItemFromIdentifiersResp(
            results={"SPGI": LineItemResp.model_validate(self.line_item_resp)},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
            notes=expected_notes,
        )

        resp = await get_financial_line_item_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            line_item="revenue",
            httpx_client=httpx_client,
            calendar_type=calendar_type,
        )

        assert resp == expected_response

    @pytest.mark.asyncio
    async def test_most_recent_request(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN we request most recent line items for multiple companies
        THEN we only get back the most recent line item for each company
        """

        company_ids = [1, 2]

        # Mock the line_item response for both companies
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/line_item/",
            json={"results": {"1": self.line_item_resp, "2": self.line_item_resp}, "errors": {}},
        )

        line_item_resp = LineItemResp.model_validate(
            {
                "currency": "USD",
                "periods": {
                    "CY2024": {
                        "period_end_date": "2024-12-31",
                        "num_months": 12,
                        "line_item": {"name": "Revenue", "value": "14208000000.0", "sources": []},
                    }
                },
            }
        )
        expected_response = GetFinancialLineItemFromIdentifiersResp(
            results={"C_1": line_item_resp, "C_2": line_item_resp},
            notes=[SOURCE_LINK_NOTE, FISCAL_PERIOD_WARNING, FISCAL_YEAR_TERMINOLOGY_WARNING],
        )

        resp = await get_financial_line_item_from_identifiers(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            line_item="revenue",
            httpx_client=httpx_client,
        )

        assert resp == expected_response

    def test_line_items_and_aliases_included_in_schema(self, mock_client: Client):
        """
        GIVEN a GetFinancialLineItemFromIdentifiers tool
        WHEN we generate an openai schema from the tool
        THEN all line items and aliases are included in the line item enum
        """
        tool = GetFinancialLineItemFromIdentifiers(kfinance_client=mock_client)
        oai_schema = convert_to_openai_tool(tool)
        line_items = oai_schema["function"]["parameters"]["properties"]["line_item"]["enum"]
        # revenue is a line item
        assert "revenue" in line_items
        # normal_revenue is an alias for revenue
        assert "normal_revenue" in line_items


class TestFindSimilarLineItems:
    """Tests for the _find_similar_line_items function."""

    # Preset test descriptors to ensure consistent results
    TEST_DESCRIPTORS = {
        "revenue": "Revenue recognized from primary business activities (excludes non-operating income).",
        "total_revenue": "Sum of operating and non-operating revenue streams for the period.",
        "cost_of_goods_sold": "Direct costs attributable to producing goods sold during the period.",
        "cogs": "Direct costs attributable to producing goods sold during the period.",
        "gross_profit": "Revenue minus cost_of_goods_sold or cost_of_revenue for the reported period.",
        "operating_income": "Operating profit after subtracting operating expenses from operating revenue.",
        "net_income": "Bottom-line profit attributable to common shareholders.",
        "research_and_development_expense": "Expenses incurred for research and development activities.",
        "r_and_d_expense": "Expenses incurred for research and development activities.",
        "depreciation_and_amortization": "Combined depreciation and amortization expense for the period.",
        "ebitda": "Earnings before interest, taxes, depreciation, and amortization.",
    }

    def test_exact_keyword_match(self):
        """
        GIVEN a preset descriptors dictionary
        WHEN searching for 'revenues' (similar to 'revenue')
        THEN 'revenue' should be in the top suggestions
        """
        results = _find_similar_line_items("revenues", self.TEST_DESCRIPTORS, max_suggestions=5)

        assert len(results) > 0
        assert isinstance(results[0], LineItemScore)
        # Check that revenue or total_revenue is in top results
        result_names = [item.name for item in results]
        assert "revenue" in result_names or "total_revenue" in result_names

    def test_acronym_matching(self):
        """
        GIVEN a preset descriptors dictionary
        WHEN searching for 'R&D' (abbreviation)
        THEN research and development related items should appear
        """
        results = _find_similar_line_items("R&D", self.TEST_DESCRIPTORS, max_suggestions=5)

        result_names = [item.name for item in results]
        # Should find r_and_d_expense or research_and_development_expense
        assert any("research" in name or "r_and_d" in name for name in result_names)

    def test_multiple_word_matching(self):
        """
        GIVEN a preset descriptors dictionary
        WHEN searching for 'cost goods'
        THEN 'cost_of_goods_sold' should be suggested
        """
        results = _find_similar_line_items("cost goods", self.TEST_DESCRIPTORS, max_suggestions=5)

        result_names = [item.name for item in results]
        assert "cost_of_goods_sold" in result_names or "cogs" in result_names

    def test_description_matching(self):
        """
        GIVEN a preset descriptors dictionary
        WHEN searching for 'profit'
        THEN items with 'profit' in description should appear
        """
        results = _find_similar_line_items("profit", self.TEST_DESCRIPTORS, max_suggestions=5)

        assert len(results) > 0
        # Should find items like gross_profit, operating_income (operating profit), or net_income
        result_names = [item.name for item in results]
        assert any("profit" in name or "income" in name for name in result_names)

    def test_empty_descriptors(self):
        """
        GIVEN an empty descriptors dictionary
        WHEN searching for any term
        THEN should return empty list
        """
        results = _find_similar_line_items("revenue", {}, max_suggestions=5)
        assert results == []

    def test_no_matches(self):
        """
        GIVEN a preset descriptors dictionary
        WHEN searching for completely unrelated term
        THEN should return empty list or very low scores filtered out
        """
        results = _find_similar_line_items("xyz123abc", self.TEST_DESCRIPTORS, max_suggestions=5)
        # Should return empty or very few results since threshold is > 0.1
        assert len(results) <= 2  # May have some weak matches but should be minimal

    def test_max_suggestions_respected(self):
        """
        GIVEN a preset descriptors dictionary
        WHEN searching with max_suggestions=3
        THEN should return at most 3 results
        """
        results = _find_similar_line_items("income", self.TEST_DESCRIPTORS, max_suggestions=3)
        assert len(results) <= 3

    def test_score_ordering(self):
        """
        GIVEN a preset descriptors dictionary
        WHEN searching for a term
        THEN results should be ordered by descending score
        """
        results = _find_similar_line_items("revenue", self.TEST_DESCRIPTORS, max_suggestions=5)

        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].score >= results[i + 1].score

    def test_score_threshold(self):
        """
        GIVEN a preset descriptors dictionary
        WHEN searching for a term
        THEN all returned results should have score > 0.1
        """
        results = _find_similar_line_items("revenue", self.TEST_DESCRIPTORS, max_suggestions=10)

        for item in results:
            assert item.score > 0.1

    def test_lineitemscore_structure(self):
        """
        GIVEN a preset descriptors dictionary
        WHEN searching for a term
        THEN each result should be a LineItemScore with name, description, and score
        """
        results = _find_similar_line_items("revenue", self.TEST_DESCRIPTORS, max_suggestions=5)

        assert len(results) > 0
        for item in results:
            assert isinstance(item, LineItemScore)
            assert isinstance(item.name, str)
            assert isinstance(item.description, str)
            assert isinstance(item.score, float)
            assert item.name in self.TEST_DESCRIPTORS
            assert item.description == self.TEST_DESCRIPTORS[item.name]
