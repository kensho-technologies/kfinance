from langchain_core.utils.function_calling import convert_to_openai_tool
from requests_mock import Mocker

from kfinance.kfinance import Client
from kfinance.models.business_relationship_models import BusinessRelationshipType
from kfinance.models.capitalization_models import Capitalization
from kfinance.models.company_models import COMPANY_ID_PREFIX
from kfinance.models.competitor_models import CompetitorSource
from kfinance.models.statement_models import StatementType
from kfinance.tests.conftest import SPGI_COMPANY_ID, SPGI_TRADING_ITEM_ID
from kfinance.tool_calling import (
    GetCusipFromIdentifiers,
    GetFinancialStatementFromIdentifiers,
    GetInfoFromIdentifiers,
    GetIsinFromIdentifiers,
    GetPricesFromIdentifiers, GetCompetitorsFromIdentifiers, GetEarningsFromIdentifiers,
)
from kfinance.tool_calling.get_business_relationship_from_identifiers import (
    GetBusinessRelationshipFromIdentifiers,
    GetBusinessRelationshipFromIdentifiersArgs,
)
from kfinance.tool_calling.get_capitalization_from_identifiers import (
    GetCapitalizationFromIdentifiers,
    GetCapitalizationFromIdentifiersArgs,
)
from kfinance.tool_calling.get_competitors_from_identifiers import GetCompetitorsFromIdentifiersArgs
from kfinance.tool_calling.get_financial_line_item_from_identifiers import (
    GetFinancialLineItemFromIdentifiers,
    GetFinancialLineItemFromIdentifiersArgs,
)
from kfinance.tool_calling.get_financial_statement_from_identifiers import (
    GetFinancialStatementFromIdentifiersArgs,
)
from kfinance.tool_calling.get_history_metadata_from_identifiers import (
    GetHistoryMetadataFromIdentifiers,
)
from kfinance.tool_calling.get_prices_from_identifiers import (
    GetPricesFromIdentifiersArgs,
)
from kfinance.tool_calling.shared_models import ToolArgsWithIdentifiers, ToolArgsWithIdentifier


class TestGetBusinessRelationshipFromIdentifiers:
    def test_get_business_relationship_from_identifiers(
        self, requests_mock: Mocker, mock_client: Client
    ):
        """
        GIVEN the GetBusinessRelationshipFromIdentifiers tool
        WHEN we request SPGI suppliers
        THEN we get back the SPGI suppliers
        """
        supplier_resp = {
            "current": [{"company_id": 883103, "company_name": "CRISIL Limited"}],
            "previous": [
                {"company_id": 472898, "company_name": "Morgan Stanley"},
                {"company_id": 8182358, "company_name": "Eloqua, Inc."},
            ],
        }
        expected_result = {
            "SPGI": {
                "current": [{"company_id": "C_883103", "company_name": "CRISIL Limited"}],
                "previous": [
                    {"company_id": "C_472898", "company_name": "Morgan Stanley"},
                    {"company_id": "C_8182358", "company_name": "Eloqua, Inc."},
                ],
            }
        }

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/relationship/{SPGI_COMPANY_ID}/supplier",
            json=supplier_resp,
        )

        tool = GetBusinessRelationshipFromIdentifiers(kfinance_client=mock_client)
        args = GetBusinessRelationshipFromIdentifiersArgs(
            identifiers=["SPGI"], business_relationship=BusinessRelationshipType.supplier
        )
        resp = tool.run(args.model_dump(mode="json"))

        assert list(resp.keys()) == ["SPGI"]
        # Sort companies by ID to make the result deterministic
        resp["SPGI"]["current"].sort(key=lambda x: x["company_id"])
        resp["SPGI"]["previous"].sort(key=lambda x: x["company_id"])
        assert resp == expected_result


class TestGetCapitalizationFromCompanyIds:
    market_caps_resp = {
        "currency": "USD",
        "market_caps": [
            {
                "date": "2024-04-10",
                "market_cap": "132766738270.000000",
                "tev": "147455738270.000000",
                "shares_outstanding": 313099562,
            },
            {
                "date": "2024-04-11",
                "market_cap": "132416066761.000000",
                "tev": "147105066761.000000",
                "shares_outstanding": 313099562,
            },
        ],
    }

    def test_get_capitalization_from_identifiers(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetCapitalizationFromIdentifiers tool
        WHEN we request the SPGI market cap
        THEN we get back the SPGI market cap
        """
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/market_cap/{SPGI_COMPANY_ID}/none/none",
            json=self.market_caps_resp,
        )

        expected_response = {
            "SPGI": [
                {"date": "2024-04-10", "market_cap": {"unit": "USD", "value": "132766738270.00"}},
                {"date": "2024-04-11", "market_cap": {"unit": "USD", "value": "132416066761.00"}},
            ]
        }

        tool = GetCapitalizationFromIdentifiers(kfinance_client=mock_client)
        args = GetCapitalizationFromIdentifiersArgs(
            identifiers=["SPGI"], capitalization=Capitalization.market_cap
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetCapitalizationFromIdentifiers tool
        WHEN we request most recent market caps for multiple companies
        THEN we only get back the most recent market cap for each company
        """
        expected_response = {
            "C_1": [
                {"date": "2024-04-10", "market_cap": {"unit": "USD", "value": "132766738270.00"}}
            ],
            "C_2": [
                {"date": "2024-04-10", "market_cap": {"unit": "USD", "value": "132766738270.00"}}
            ],
        }

        company_ids = [1, 2]
        for company_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/market_cap/{company_id}/none/none",
                json=self.market_caps_resp,
            )
        tool = GetCapitalizationFromIdentifiers(kfinance_client=mock_client)
        args = GetCapitalizationFromIdentifiersArgs(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            capitalization=Capitalization.market_cap,
        )

        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response


class TestGetCusipFromIdentifiers:
    def test_get_cusip_from_identifiers(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetCusipFromIdentifiers tool
        WHEN we request the CUSIPs for multiple companies
        THEN we get back the corresponding CUSIPs
        """

        company_ids = [1, 2]
        expected_response = {"C_1": "CU1", "C_2": "CU2"}
        for security_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/cusip/{security_id}",
                json={"cusip": f"CU{security_id}"},
            )
        tool = GetCusipFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run(
            ToolArgsWithIdentifiers(
                identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids]
            ).model_dump(mode="json")
        )
        assert resp == expected_response


class TestGetIsinFromSecurityIds:
    def test_get_isin_from_security_ids(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetIsinFromSecurityIds tool
        WHEN we request the ISINs for multiple security ids
        THEN we get back the corresponding ISINs
        """

        company_ids = [1, 2]
        expected_response = {"C_1": "IS1", "C_2": "IS2"}
        for security_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/isin/{security_id}",
                json={"isin": f"IS{security_id}"},
            )
        tool = GetIsinFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run(
            ToolArgsWithIdentifiers(
                identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids]
            ).model_dump(mode="json")
        )
        assert resp == expected_response


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


class TestGetFinancialStatementFromIdentifiers:
    statement_resp = {
        "statements": {
            "2020": {"Revenues": "7442000000.000000", "Total Revenues": "7442000000.000000"},
            "2021": {"Revenues": "8243000000.000000", "Total Revenues": "8243000000.000000"},
        }
    }

    def test_get_financial_statement_from_identifiers(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN the GetFinancialLineItemFromIdentifiers tool
        WHEN we request the SPGI income statement
        THEN we get back the SPGI income statement
        """

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/statements/{SPGI_COMPANY_ID}/income_statement/none/none/none/none/none",
            json=self.statement_resp,
        )
        expected_response = {
            "SPGI": {
                "Revenues": {"2020": 7442000000.0, "2021": 8243000000.0},
                "Total Revenues": {"2020": 7442000000.0, "2021": 8243000000.0},
            }
        }

        tool = GetFinancialStatementFromIdentifiers(kfinance_client=mock_client)
        args = GetFinancialStatementFromIdentifiersArgs(
            identifiers=["SPGI"], statement=StatementType.income_statement
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetFinancialLineItemFromIdentifiers tool
        WHEN we request most recent statement for multiple companies
        THEN we only get back the most recent statement for each company
        """

        company_ids = [1, 2]
        expected_response = {
            "C_1": {"Revenues": {"2021": 8243000000.0}, "Total Revenues": {"2021": 8243000000.0}},
            "C_2": {"Revenues": {"2021": 8243000000.0}, "Total Revenues": {"2021": 8243000000.0}},
        }

        for company_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/statements/{company_id}/income_statement/none/none/none/none/none",
                json=self.statement_resp,
            )

        tool = GetFinancialStatementFromIdentifiers(kfinance_client=mock_client)
        args = GetFinancialStatementFromIdentifiersArgs(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            statement=StatementType.income_statement,
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response


class TestGetHistoryMetadataFromIdentifiers:
    def test_get_history_metadata_from_identifiers(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN the GetHistoryMetadataFromIdentifiers tool
        WHEN we request the history metadata for SPGI
        THEN we get back SPGI's history metadata
        """
        metadata_resp = {
            "currency": "USD",
            "exchange_name": "NYSE",
            "first_trade_date": "1968-01-02",
            "instrument_type": "Equity",
            "symbol": "SPGI",
        }
        expected_resp = {"SPGI": metadata_resp}

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/pricing/{SPGI_TRADING_ITEM_ID}/metadata",
            json=metadata_resp,
        )

        tool = GetHistoryMetadataFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run(ToolArgsWithIdentifiers(identifiers=["SPGI"]).model_dump(mode="json"))
        assert resp == expected_resp


class TestGetInfoFromIdentifiers:
    def test_get_info_from_identifiers(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetInfoFromIdentifiers tool
        WHEN request info for SPGI
        THEN we get back info for SPGI
        """

        info_resp = {"name": "S&P Global Inc.", "status": "Operating"}
        expected_response = {"SPGI": info_resp}
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/info/{SPGI_COMPANY_ID}",
            json=info_resp,
        )

        tool = GetInfoFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run(ToolArgsWithIdentifiers(identifiers=["SPGI"]).model_dump(mode="json"))
        assert resp == expected_response


class TestPricesFromIdentifiers:
    prices_resp = {
        "currency": "USD",
        "prices": [
            {
                "date": "2024-04-11",
                "open": "424.260000",
                "high": "425.990000",
                "low": "422.040000",
                "close": "422.920000",
                "volume": "1129158",
            },
            {
                "date": "2024-04-12",
                "open": "419.230000",
                "high": "421.940000",
                "low": "416.450000",
                "close": "417.810000",
                "volume": "1182229",
            },
        ],
    }

    def test_get_prices_from_identifiers(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetPricesFromIdentifiers tool
        WHEN we request prices for SPGI
        THEN we get back prices for SPGI
        """

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/pricing/{SPGI_TRADING_ITEM_ID}/none/none/day/adjusted",
            json=self.prices_resp,
        )
        expected_response = {
            "SPGI": {
                "prices": [
                    {
                        "date": "2024-04-11",
                        "open": {"value": "424.26", "unit": "USD"},
                        "high": {"value": "425.99", "unit": "USD"},
                        "low": {"value": "422.04", "unit": "USD"},
                        "close": {"value": "422.92", "unit": "USD"},
                        "volume": {"value": "1129158", "unit": "Shares"},
                    },
                    {
                        "date": "2024-04-12",
                        "open": {"value": "419.23", "unit": "USD"},
                        "high": {"value": "421.94", "unit": "USD"},
                        "low": {"value": "416.45", "unit": "USD"},
                        "close": {"value": "417.81", "unit": "USD"},
                        "volume": {"value": "1182229", "unit": "Shares"},
                    },
                ]
            }
        }

        tool = GetPricesFromIdentifiers(kfinance_client=mock_client)
        response = tool.run(
            GetPricesFromIdentifiersArgs(identifiers=["SPGI"]).model_dump(mode="json")
        )
        assert response == expected_response

    def test_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetPricesFromIdentifiers tool
        WHEN we request most recent prices for multiple companies
        THEN we only get back the most recent prices for each company
        """

        company_ids = [1, 2]
        for trading_item_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/pricing/{trading_item_id}/none/none/day/adjusted",
                json=self.prices_resp,
            )

        expected_single_company_response = {
            "prices": [
                {
                    "date": "2024-04-11",
                    "open": {"value": "424.26", "unit": "USD"},
                    "high": {"value": "425.99", "unit": "USD"},
                    "low": {"value": "422.04", "unit": "USD"},
                    "close": {"value": "422.92", "unit": "USD"},
                    "volume": {"value": "1129158", "unit": "Shares"},
                }
            ]
        }
        expected_response = {
            "C_1": expected_single_company_response,
            "C_2": expected_single_company_response,
        }
        tool = GetPricesFromIdentifiers(kfinance_client=mock_client)
        response = tool.run(
            GetPricesFromIdentifiersArgs(
                identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids]
            ).model_dump(mode="json")
        )
        assert response == expected_response


class TestGetCompetitorsFromIdentifiers:
    def test_get_competitors_from_identifiers(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetCompetitorsFromIdentifiers tool
        WHEN we request the SPGI competitors that are named by competitors
        THEN we get back the SPGI competitors that are named by competitors
        """
        competitors_response = {
            "companies": [
                {"company_id": 35352, "company_name": "The Descartes Systems Group Inc."},
                {"company_id": 4003514, "company_name": "London Stock Exchange Group plc"},
            ]
        }
        expected_response = {"SPGI": [
                {"company_id": 35352, "company_name": "The Descartes Systems Group Inc."},
                {"company_id": 4003514, "company_name": "London Stock Exchange Group plc"},
            ]}


        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/competitors/{SPGI_COMPANY_ID}/named_by_competitor",
            # truncated from the original API response
            json=competitors_response,
        )

        tool = GetCompetitorsFromIdentifiers(kfinance_client=mock_client)
        args = GetCompetitorsFromIdentifiersArgs(
            identifiers=["SPGI"], competitor_source=CompetitorSource.named_by_competitor
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response


class TestGetEarnings:
    def test_get_earnings(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetEarnings tool
        WHEN we request all earnings for SPGI
        THEN we get back all SPGI earnings
        """
        earnings_data = {
            "earnings": [
                {
                    "name": "SPGI Q1 2025 Earnings Call",
                    "datetime": "2025-04-29T12:30:00Z",
                    "key_dev_id": 12346,
                },
                {
                    "name": "SPGI Q4 2024 Earnings Call",
                    "datetime": "2025-02-11T13:30:00Z",
                    "key_dev_id": 12345,
                },
            ]
        }

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/earnings/{SPGI_COMPANY_ID}",
            json=earnings_data,
        )

        expected_response = {'SPGI': [{'datetime': '2025-04-29T12:30:00Z', 'key_dev_id': 12346, 'name': 'SPGI Q1 2025 Earnings Call'}, {'datetime': '2025-02-11T13:30:00Z', 'key_dev_id': 12345, 'name': 'SPGI Q4 2024 Earnings Call'}]}

        tool = GetEarningsFromIdentifiers(kfinance_client=mock_client)
        response = tool.run(ToolArgsWithIdentifiers(identifiers=["SPGI"]).model_dump(mode="json"))
        assert response == expected_response