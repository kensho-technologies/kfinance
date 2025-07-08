from copy import deepcopy
from datetime import date

from langchain_core.utils.function_calling import convert_to_openai_tool
from requests_mock import Mocker

from kfinance.constants import BusinessRelationshipType, Capitalization, StatementType, COMPANY_ID_PREFIX
from kfinance.kfinance import Client
from kfinance.tests.conftest import SPGI_COMPANY_ID, SPGI_SECURITY_ID, SPGI_TRADING_ITEM_ID
from kfinance.tool_calling import (
    GetCusipFromIdentifiers,
    GetEarningsCallDatetimesFromIdentifiers,
    GetFinancialStatementFromIdentifiers,
    GetInfoFromIdentifiers,
    GetIsinFromIdentifiers,
    GetPricesFromIdentifiers,
)
from kfinance.tool_calling.get_business_relationship_from_identifier import (
    GetBusinessRelationshipFromIdentifiers, GetBusinessRelationshipFromIdentifiersArgs,
)
from kfinance.tool_calling.get_capitalization_from_identifiers import (
    GetCapitalizationFromIdentifiers, GetCapitalizationFromIdentifiersArgs,
)

from kfinance.tool_calling.get_financial_line_item_from_identifiers import (
    GetFinancialLineItemFromIdentifiersArgs,
)
from kfinance.tool_calling.get_financial_statement_from_identifiers import (
    GetFinancialStatementFromIdentifiersArgs,
)
from kfinance.tool_calling.get_history_metadata_from_identifiers import (
    GetHistoryMetadataFromIdentifiers,
)
from kfinance.tool_calling.get_isin_from_identifiers import GetIsinFromSecurityIdsArgs
from kfinance.tool_calling.get_prices_from_identifiers import (
    GetPricesFromIdentifiersArgs,
)


class TestGetBusinessRelationshipFromCompanyId:
    def test_get_business_relationship_from_identifiers(
        self, requests_mock: Mocker, mock_client: Client
    ):
        """
        GIVEN the GetBusinessRelationshipFromIdentifier tool
        WHEN we request SPGI suppliers
        THEN we get back the SPGI suppliers
        """
        supplier_resp = {
    "current": [
        {
            "company_id": 883103,
            "company_name": "CRISIL Limited"
        }
    ],
    "previous": [
        {
            "company_id": 472898,
            "company_name": "Morgan Stanley"
        },
        {
            "company_id": 8182358,
            "company_name": "Eloqua, Inc."
        },
        ]
        }
        expected_result = {'SPGI': {'current': [{'company_id': 'C_883103', 'company_name': 'CRISIL Limited'}], 'previous': [{'company_id': 'C_472898', 'company_name': 'Morgan Stanley'}, {'company_id': 'C_8182358', 'company_name': 'Eloqua, Inc.'}]}}

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
        ]
    }

    def test_get_capitalization_from_identifiers(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetCapitalizationFromCompanyIds tool
        WHEN we request the SPGI market cap
        THEN we get back the SPGI market cap
        """
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/market_cap/{SPGI_COMPANY_ID}/none/none",
            json=self.market_caps_resp,
        )

        expected_response = {'SPGI': {'market_cap': {'2024-04-10': 132766738270.0, '2024-04-11': 132416066761.0}}}

        tool = GetCapitalizationFromIdentifiers(kfinance_client=mock_client)
        args = GetCapitalizationFromIdentifiersArgs(
            identifiers=["SPGI"], capitalization=Capitalization.market_cap
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetCapitalizationFromCompanyIds tool
        WHEN we request most recent market caps for multiple companies
        THEN we only get back the most recent market cap for each company
        """
        expected_response = {'C_1': {'market_cap': {'2024-04-11': 132416066761.0}}, 'C_2': {'market_cap': {'2024-04-11': 132416066761.0}}}

        company_ids = [1, 2]
        for company_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/market_cap/{company_id}/none/none",
                json=self.market_caps_resp,
            )
        tool = GetCapitalizationFromIdentifiers(kfinance_client=mock_client)
        args = GetCapitalizationFromIdentifiersArgs(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids], capitalization=Capitalization.market_cap
        )

        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response


class TestGetCusipFromSecurityIds:
    def test_get_cusip_from_security_ids(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetCusipFromSecurityIds tool
        WHEN we request the CUSIPs for multiple security ids
        THEN we get back the corresponding CUSIPs
        """

        security_ids = [1, 2]
        expected_response = {"security_id: 1": "CUSIP: 1", "security_id: 2": "CUSIP: 2"}
        for security_id in security_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/cusip/{security_id}",
                json={"cusip": security_id},
            )
        tool = GetCusipFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run(
            GetCusipFromSecurityIdsArgs(security_ids=security_ids).model_dump(mode="json")
        )
        assert resp == expected_response


class TestGetIsinFromSecurityIds:
    def test_get_isin_from_security_ids(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetIsinFromSecurityIds tool
        WHEN we request the ISINs for multiple security ids
        THEN we get back the corresponding ISINs
        """

        security_ids = [1, 2]
        expected_response = {"security_id: 1": "ISIN: 1", "security_id: 2": "ISIN: 2"}
        for security_id in security_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/isin/{security_id}",
                json={"isin": security_id},
            )
        tool = GetIsinFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run(
            GetIsinFromSecurityIdsArgs(security_ids=security_ids).model_dump(mode="json")
        )
        assert resp == expected_response


class TestGetEarningsCallDatetimesFromCompanyIds:
    def test_get_earnings_call_datetimes_from_company_ids(
        self, requests_mock: Mocker, mock_client: Client
    ):
        """
        GIVEN the GetEarningsCallDatetimesFromCompanyIds tool
        WHEN we request earnings call datetimes for multiple companies
        THEN we get back the expected earnings call datetimes
        """
        company_ids = [1, 2]
        expected_response = {
            "company_id: 1": ["2025-04-29T12:30:00+00:00", "2025-02-11T13:30:00+00:00"],
            "company_id: 2": ["2025-04-29T12:30:00+00:00", "2025-02-11T13:30:00+00:00"],
        }
        for company_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/earnings/{company_id}/dates",
                json={"earnings": ["2025-04-29T12:30:00", "2025-02-11T13:30:00"]},
            )
        tool = GetEarningsCallDatetimesFromIdentifiers(kfinance_client=mock_client)
        response = tool.run(
            GetEarningsCallDatetimesFromCompanyIdsArgs(company_ids=company_ids).model_dump(
                mode="json"
            )
        )
        assert response == expected_response


class TestGetFinancialLineItemFromCompanyIds:
    line_item_resp = {
        "line_item": {
            "2022": "11181000000.000000",
            "2023": "12497000000.000000",
            "2024": "14208000000.000000",
        }
    }

    def test_get_financial_line_item_from_company_ids(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN the GetFinancialLineItemFromCompanyId tool
        WHEN we request SPGI revenue
        THEN we get back the SPGI revenue
        """

        expected_response = {
            "company_id: 21719": "{'2022': {'revenue': 11181000000.0}, '2023': {'revenue': 12497000000.0}, '2024': {'revenue': 14208000000.0}}"
        }

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/line_item/{SPGI_COMPANY_ID}/revenue/none/none/none/none/none",
            json=self.line_item_resp,
        )

        tool = GetFinancialLineItemFromIdentifiersIds(kfinance_client=mock_client)
        args = GetFinancialLineItemFromIdentifiersArgs(
            company_ids=[SPGI_COMPANY_ID], line_item="revenue"
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetFinancialLineItemFromCompanyIds tool
        WHEN we request most recent line items for multiple companies
        THEN we only get back the most recent line item for each company
        """

        company_ids = [1, 2]
        expected_response = {
            "company_id: 1": "{'2024': {'revenue': 14208000000.0}}",
            "company_id: 2": "{'2024': {'revenue': 14208000000.0}}",
        }
        for company_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/line_item/{company_id}/revenue/none/none/none/none/none",
                json=self.line_item_resp,
            )
        tool = GetFinancialLineItemFromIdentifiersIds(kfinance_client=mock_client)
        args = GetFinancialLineItemFromIdentifiersArgs(company_ids=company_ids, line_item="revenue")
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_line_items_and_aliases_included_in_schema(self, mock_client: Client):
        """
        GIVEN a GetFinancialLineItemFromCompanyIds tool
        WHEN we generate an openai schema from the tool
        THEN all line items and aliases are included in the line item enum
        """
        tool = GetFinancialLineItemFromIdentifiersIds(kfinance_client=mock_client)
        oai_schema = convert_to_openai_tool(tool)
        line_items = oai_schema["function"]["parameters"]["properties"]["line_item"]["enum"]
        # revenue is a line item
        assert "revenue" in line_items
        # normal_revenue is an alias for revenue
        assert "normal_revenue" in line_items


class TestGetFinancialStatementFromCompanyId:
    statement_resp = {
        "statements": {
            "2020": {"Revenues": "7442000000.000000", "Total Revenues": "7442000000.000000"},
            "2021": {"Revenues": "8243000000.000000", "Total Revenues": "8243000000.000000"},
        }
    }

    def test_get_financial_statement_from_company_id(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN the GetFinancialLineItemFromCompanyIds tool
        WHEN we request the SPGI income statement
        THEN we get back the SPGI income statement
        """

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/statements/{SPGI_COMPANY_ID}/income_statement/none/none/none/none/none",
            json=self.statement_resp,
        )
        expected_response = {
            "company_id: 21719": "{'2020': {'Revenues': 7442000000.0, 'Total Revenues': 7442000000.0}, '2021': {'Revenues': 8243000000.0, 'Total Revenues': 8243000000.0}}"
        }

        tool = GetFinancialStatementFromIdentifiers(kfinance_client=mock_client)
        args = GetFinancialStatementFromIdentifiersArgs(
            company_ids=[SPGI_COMPANY_ID], statement=StatementType.income_statement
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetFinancialLineItemFromCompanyIds tool
        WHEN we request most recent statement for multiple companies
        THEN we only get back the most recent statement for each company
        """

        company_ids = [1, 2]
        expected_response = {
            "company_id: 1": "{'2021': {'Revenues': 8243000000.0, 'Total Revenues': 8243000000.0}}",
            "company_id: 2": "{'2021': {'Revenues': 8243000000.0, 'Total Revenues': 8243000000.0}}",
        }

        for company_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/statements/{company_id}/income_statement/none/none/none/none/none",
                json=self.statement_resp,
            )

        tool = GetFinancialStatementFromIdentifiers(kfinance_client=mock_client)
        args = GetFinancialStatementFromIdentifiersArgs(
            company_ids=company_ids, statement=StatementType.income_statement
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response


class TestGetHistoryMetadataFromTradingItemIds:
    def test_get_history_metadata_from_trading_item_ids(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN the GetHistoryMetadataFromTradingItemIds tool
        WHEN request history metadata for multiple trading items
        THEN we get back their history metadata
        """
        trading_item_ids = [1, 2]
        metadata_resp = {
            "currency": "USD",
            "exchange_name": "NYSE",
            "first_trade_date": "1968-01-02",
            "instrument_type": "Equity",
            "symbol": "SPGI",
        }

        expected_single_resp = deepcopy(metadata_resp)
        expected_single_resp["first_trade_date"] = date(1968, 1, 2)
        expected_resp = {
            "trading_item_id: 1": expected_single_resp,
            "trading_item_id: 2": expected_single_resp,
        }

        for trading_item_id in trading_item_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/pricing/{trading_item_id}/metadata",
                json=metadata_resp,
            )

        tool = GetHistoryMetadataFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run(
            GetHistoryMetadataFromIdentifiersArgs(trading_item_ids=trading_item_ids).model_dump(
                mode="json"
            )
        )
        assert resp == expected_resp


class TestGetInfoFromCompanyIds:
    def test_get_info_from_company_ids(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetInfoFromCompanyIds tool
        WHEN request info for SPGI
        THEN we get back info for SPGI
        """

        info_resp = {"name": "S&P Global Inc.", "status": "Operating"}
        expected_response = {
            "company_id: 21719": {"name": "S&P Global Inc.", "status": "Operating"}
        }
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/info/{SPGI_COMPANY_ID}",
            json=info_resp,
        )

        tool = GetInfoFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run(
            GetInfoFromCompanyIdsArgs(company_ids=[SPGI_COMPANY_ID]).model_dump(mode="json")
        )
        assert resp == expected_response


class TestPricesFromTradingItemIds:
    prices_resp = {
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
        ]
    }

    def test_get_prices_from_trading_item_ids(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetPricesFromTradingItemIds tool
        WHEN we request prices for SPGI
        THEN we get back prices for SPGI
        """

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/pricing/{SPGI_TRADING_ITEM_ID}/none/none/day/adjusted",
            json=self.prices_resp,
        )
        expected_response = {
            "trading_item_id: 2629108": "| date       |   open |   high |    low |   close |      volume |\n|:-----------|-------:|-------:|-------:|--------:|------------:|\n| 2024-04-11 | 424.26 | 425.99 | 422.04 |  422.92 | 1.12916e+06 |\n| 2024-04-12 | 419.23 | 421.94 | 416.45 |  417.81 | 1.18223e+06 |"
        }

        tool = GetPricesFromIdentifiers(kfinance_client=mock_client)
        response = tool.run(
            GetPricesFromIdentifiersArgs(trading_item_ids=[SPGI_TRADING_ITEM_ID]).model_dump(
                mode="json"
            )
        )
        assert response == expected_response

    def test_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetPricesFromTradingItemIds tool
        WHEN we request most recent prices for multiple companies
        THEN we only get back the most recent prices for each company
        """

        trading_item_ids = [1, 2]
        for trading_item_id in trading_item_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/pricing/{trading_item_id}/none/none/day/adjusted",
                json=self.prices_resp,
            )

        expected_single_company_response = "{'2024-04-12': {'open': 419.23, 'high': 421.94, 'low': 416.45, 'close': 417.81, 'volume': 1182229}}"
        expected_response = {
            "trading_item_id: 1": expected_single_company_response,
            "trading_item_id: 2": expected_single_company_response,
        }
        tool = GetPricesFromIdentifiers(kfinance_client=mock_client)
        response = tool.run(
            GetPricesFromIdentifiersArgs(trading_item_ids=trading_item_ids).model_dump(
                mode="json"
            )
        )
        assert response == expected_response


class TestResolveIdentifiers:
    def test_resolve_identifiers(self, mock_client: Client):
        """
        GIVEN the ResolveIdentifiers tool
        WHEN request to resolve SPGI
        THEN we get back a dict with the SPGI company id, security id, and trading item id
        """
        tool = ResolveIdentifiers(kfinance_client=mock_client)
        resp = tool.run(ResolveIdentifiersArgs(identifiers=["SPGI"]).model_dump(mode="json"))
        assert resp == {
            "SPGI": {
                "company_id": SPGI_COMPANY_ID,
                "security_id": SPGI_SECURITY_ID,
                "trading_item_id": SPGI_TRADING_ITEM_ID,
            }
        }
