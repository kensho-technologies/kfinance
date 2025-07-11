from langchain_core.utils.function_calling import convert_to_openai_tool
from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_COMPANY_ID
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX
from kfinance.domains.line_items.line_item_tools import (
    GetFinancialLineItemFromIdentifiers,
    GetFinancialLineItemFromIdentifiersArgs,
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
        WHEN we request SPGI revenue
        THEN we get back the SPGI revenue
        """

        expected_response = {
            "SPGI": {
                "2022": {"revenue": 11181000000.0},
                "2023": {"revenue": 12497000000.0},
                "2024": {"revenue": 14208000000.0},
            }
        }

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/line_item/{SPGI_COMPANY_ID}/revenue/none/none/none/none/none",
            json=self.line_item_resp,
        )

        tool = GetFinancialLineItemFromIdentifiers(kfinance_client=mock_client)
        args = GetFinancialLineItemFromIdentifiersArgs(identifiers=["SPGI"], line_item="revenue")
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetFinancialLineItemFromIdentifiers tool
        WHEN we request most recent line items for multiple companies
        THEN we only get back the most recent line item for each company
        """

        company_ids = [1, 2]
        expected_response = {
            "C_1": {"2024": {"revenue": 14208000000.0}},
            "C_2": {"2024": {"revenue": 14208000000.0}},
        }
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
