from decimal import Decimal

from langchain_core.utils.function_calling import convert_to_openai_tool
from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_COMPANY_ID
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX
from kfinance.domains.line_items.line_item_models import LineItemResponse, LineItemScore
from kfinance.domains.line_items.line_item_tools import (
    GetFinancialLineItemFromIdentifiers,
    GetFinancialLineItemFromIdentifiersArgs,
    GetFinancialLineItemFromIdentifiersResp,
    _find_similar_line_items,
)


class TestGetFinancialLineItemFromCompanyIds:
    line_item_resp = {
        "line_item": {
            "2022": "11181000000.000000",
            "2023": "12497000000.000000",
            "2024": "14208000000.000000",
        }
    }

    def test_get_financial_line_item_from_identifiers(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN the GetFinancialLineItemFromCompanyId tool
        WHEN we request revenue for SPGI and a non-existent company
        THEN we get back the SPGI revenue and an error for the non-existent company
        """

        expected_response = GetFinancialLineItemFromIdentifiersResp(
            results={
                "SPGI": LineItemResponse(
                    line_item={
                        "2022": Decimal(11181000000),
                        "2023": Decimal(12497000000),
                        "2024": Decimal(14208000000),
                    }
                )
            },
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/line_item/{SPGI_COMPANY_ID}/revenue/none/none/none/none/none",
            json=self.line_item_resp,
        )

        tool = GetFinancialLineItemFromIdentifiers(kfinance_client=mock_client)
        args = GetFinancialLineItemFromIdentifiersArgs(
            identifiers=["SPGI", "non-existent"], line_item="revenue"
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetFinancialLineItemFromIdentifiers tool
        WHEN we request most recent line items for multiple companies
        THEN we only get back the most recent line item for each company
        """

        company_ids = [1, 2]

        line_item_resp = LineItemResponse(line_item={"2024": Decimal(14208000000)})
        expected_response = GetFinancialLineItemFromIdentifiersResp(
            results={"C_1": line_item_resp, "C_2": line_item_resp},
        )

        for company_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/line_item/{company_id}/revenue/none/none/none/none/none",
                json=self.line_item_resp,
            )
        tool = GetFinancialLineItemFromIdentifiers(kfinance_client=mock_client)
        args = GetFinancialLineItemFromIdentifiersArgs(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            line_item="revenue",
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_empty_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetFinancialLineItemFromIdentifiers tool
        WHEN we request most recent line items for multiple companies
        THEN we only get back the most recent line item for each company
        UNLESS no line items exist
        """

        company_ids = [1, 2]

        c_1_line_item_resp = LineItemResponse(line_item={})
        c_2_line_item_resp = LineItemResponse(line_item={"2024": Decimal(14208000000)})
        expected_response = GetFinancialLineItemFromIdentifiersResp(
            results={"C_1": c_1_line_item_resp, "C_2": c_2_line_item_resp},
        )

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/line_item/1/revenue/none/none/none/none/none",
            json={"line_item": {}},
        )
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/line_item/2/revenue/none/none/none/none/none",
            json=self.line_item_resp,
        )
        tool = GetFinancialLineItemFromIdentifiers(kfinance_client=mock_client)
        args = GetFinancialLineItemFromIdentifiersArgs(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            line_item="revenue",
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_line_items_and_aliases_included_in_schema(self, mock_client: Client):
        """
        GIVEN a GetFinancialLineItemFromCompanyIds tool
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
