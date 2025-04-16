from datetime import date, datetime

from langchain_core.utils.function_calling import convert_to_openai_tool
import pytest
from requests_mock import Mocker
import time_machine

from kfinance.constants import BusinessRelationshipType, Capitalization, StatementType
from kfinance.kfinance import Client
from kfinance.tool_calling import (
    GetCompanyIdFromIdentifier,
    GetEarningsCallDatetimesFromIdentifier,
    GetFinancialLineItemFromIdentifier,
    GetFinancialStatementFromIdentifier,
    GetHistoryMetadataFromIdentifier,
    GetInfoFromIdentifier,
    GetIsinFromTicker,
    GetLatest,
    GetNQuartersAgo,
    GetPricesFromIdentifier,
    GetSecurityIdFromIdentifier,
    GetTradingItemIdFromIdentifier,
)
from kfinance.tool_calling.get_business_relationship_from_identifier import (
    GetBusinessRelationshipFromIdentifier,
    GetBusinessRelationshipFromIdentifierArgs,
)
from kfinance.tool_calling.get_capitalization_from_identifier import (
    GetCapitalizationFromIdentifier,
    GetCapitalizationFromIdentifierArgs,
)
from kfinance.tool_calling.get_cusip_from_ticker import GetCusipFromTicker, GetCusipFromTickerArgs
from kfinance.tool_calling.get_financial_line_item_from_identifier import (
    GetFinancialLineItemFromIdentifierArgs,
)
from kfinance.tool_calling.get_financial_statement_from_identifier import (
    GetFinancialStatementFromIdentifierArgs,
)
from kfinance.tool_calling.get_isin_from_ticker import GetIsinFromTickerArgs
from kfinance.tool_calling.get_latest import GetLatestArgs
from kfinance.tool_calling.get_n_quarters_ago import GetNQuartersAgoArgs
from kfinance.tool_calling.get_prices_from_identifier import GetPricesFromIdentifierArgs
from kfinance.tool_calling.shared_models import ToolArgsWithIdentifier


SPGI_COMPANY_ID = 21719
SPGI_SECURITY_ID = 2629107
SPGI_TRADING_ITEM_ID = 2629108


@pytest.fixture
def mock_client(requests_mock: Mocker) -> Client:
    """Create a KFinanceApiClient with a mock response for the SPGI id triple."""

    client = Client(refresh_token="foo")
    # Set access token so that the client doesn't try to fetch it.
    client.kfinance_api_client._access_token = "foo"  # noqa: SLF001
    client.kfinance_api_client._access_token_expiry = datetime(2100, 1, 1).timestamp()  # noqa: SLF001

    # Create a mock for the SPGI id triple.
    requests_mock.get(
        url="https://kfinance.kensho.com/api/v1/id/SPGI",
        json={
            "trading_item_id": SPGI_TRADING_ITEM_ID,
            "security_id": SPGI_SECURITY_ID,
            "company_id": SPGI_COMPANY_ID,
        },
    )
    return client


class TestGetBusinessRelationshipFromIdentifier:
    def test_get_business_relationship_from_identifier(
        self, requests_mock: Mocker, mock_client: Client
    ):
        """
        GIVEN the GetBusinessRelationshipFromIdentifier tool
        WHEN we request SPGI suppliers
        THEN we get back the SPGI suppliers
        """
        supplier_resp = {"current": [883103], "previous": [472898, 8182358]}

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/relationship/{SPGI_COMPANY_ID}/supplier",
            json=supplier_resp,
        )

        tool = GetBusinessRelationshipFromIdentifier(kfinance_client=mock_client)
        args = GetBusinessRelationshipFromIdentifierArgs(
            identifier="SPGI", business_relationship=BusinessRelationshipType.supplier
        )
        resp = tool.run(args.model_dump(mode="json"))
        # Companies is a set, so we have to sort the result
        resp["previous"].sort()
        assert resp == supplier_resp


class TestGetCapitalizationFromIdentifier:
    def test_get_capitalization_from_identifier(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetCapitalizationFromIdentifier tool
        WHEN we request the SPGI market cap
        THEN we get back the SPGI market cap
        """

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/market_cap/{SPGI_COMPANY_ID}/none/none",
            json={
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
            },
        )

        expected_response = "| date       |   market_cap |\n|:-----------|-------------:|\n| 2024-04-10 |  1.32767e+11 |\n| 2024-04-11 |  1.32416e+11 |"

        tool = GetCapitalizationFromIdentifier(kfinance_client=mock_client)
        args = GetCapitalizationFromIdentifierArgs(
            identifier="SPGI", capitalization=Capitalization.market_cap
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response


class TestGetCompanyIdFromIdentifier:
    def test_get_company_id_from_identifier(self, mock_client: Client):
        """
        GIVEN the GetCompanyIdFromIdentifier tool
        WHEN request the company id for SPGI
        THEN we get back the SPGI company id
        """
        tool = GetCompanyIdFromIdentifier(kfinance_client=mock_client)
        resp = tool.run(ToolArgsWithIdentifier(identifier="SPGI").model_dump(mode="json"))
        assert resp == SPGI_COMPANY_ID


class TestGetCusipFromTicker:
    def test_get_cusip_from_ticker(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetCusipFromTicker tool
        WHEN we pass args with the SPGI ticker
        THEN we get back the SPGI cusip
        """

        spgi_cusip = "78409V104"
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/cusip/{SPGI_SECURITY_ID}",
            json={"cusip": spgi_cusip},
        )
        tool = GetCusipFromTicker(kfinance_client=mock_client)
        resp = tool.run(GetCusipFromTickerArgs(ticker_str="SPGI").model_dump(mode="json"))
        assert resp == spgi_cusip


class TestGetEarningsCallDatetimesFromTicker:
    def test_get_earnings_call_datetimes_from_ticker(
        self, requests_mock: Mocker, mock_client: Client
    ):
        """
        GIVEN the GetEarningsCallDatetimesFromIdentifier tool
        WHEN we request earnings call datetimes for SPGI
        THEN we get back the expected SPGI earnings call datetimes
        """

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/earnings/{SPGI_COMPANY_ID}/dates",
            json={"earnings": ["2025-04-29T12:30:00", "2025-02-11T13:30:00"]},
        )
        expected_response = '["2025-04-29T12:30:00+00:00", "2025-02-11T13:30:00+00:00"]'

        tool = GetEarningsCallDatetimesFromIdentifier(kfinance_client=mock_client)
        response = tool.run(ToolArgsWithIdentifier(identifier="SPGI").model_dump(mode="json"))
        assert response == expected_response


class TestGetFinancialLineItemFromIdentifier:
    def test_get_financial_line_item_from_identifier(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN the GetFinancialLineItemFromIdentifier tool
        WHEN we request SPGI revenue
        THEN we get back the SPGI revenue
        """

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/line_item/{SPGI_COMPANY_ID}/revenue/none/none/none/none/none",
            json={
                "line_item": {
                    "2020": "7442000000.000000",
                    "2021": "8297000000.000000",
                    "2022": "11181000000.000000",
                    "2023": "12497000000.000000",
                    "2024": "14208000000.000000",
                }
            },
        )
        expected_response = "|         |      2020 |      2021 |       2022 |       2023 |       2024 |\n|:--------|----------:|----------:|-----------:|-----------:|-----------:|\n| revenue | 7.442e+09 | 8.297e+09 | 1.1181e+10 | 1.2497e+10 | 1.4208e+10 |"

        tool = GetFinancialLineItemFromIdentifier(kfinance_client=mock_client)
        args = GetFinancialLineItemFromIdentifierArgs(identifier="SPGI", line_item="revenue")
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_line_items_and_aliases_included_in_schema(self, mock_client: Client):
        """
        GIVEN a GetFinancialLineItemFromIdentifier tool
        WHEN we generate an openai schema from the tool
        THEN all line items and aliases are included in the line item enum
        """
        tool = GetFinancialLineItemFromIdentifier(kfinance_client=mock_client)
        oai_schema = convert_to_openai_tool(tool)
        line_items = oai_schema["function"]["parameters"]["properties"]["line_item"]["enum"]
        # revenue is a line item
        assert "revenue" in line_items
        # normal_revenue is an alias for revenue
        assert "normal_revenue" in line_items


class TestGetFinancialStatementFromIdentifier:
    def test_get_financial_statement_from_identifier(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN the GetFinancialLineItemFromIdentifier tool
        WHEN we request the SPGI income statement
        THEN we get back the SPGI income statement
        """

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/statements/{SPGI_COMPANY_ID}/income_statement/none/none/none/none/none",
            # truncated from the original API response
            json={
                "statements": {
                    "2020": {"Revenues": "7442000000.000000", "Total Revenues": "7442000000.000000"}
                }
            },
        )
        expected_response = "|                |      2020 |\n|:---------------|----------:|\n| Revenues       | 7.442e+09 |\n| Total Revenues | 7.442e+09 |"

        tool = GetFinancialStatementFromIdentifier(kfinance_client=mock_client)
        args = GetFinancialStatementFromIdentifierArgs(
            identifier="SPGI", statement=StatementType.income_statement
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response


class TestGetHistoryMetadataFromIdentifier:
    def test_get_history_metadata_from_identifier(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetHistoryMetadataFromIdentifier tool
        WHEN request history metadata for SPGI
        THEN we get back the SPGI history metadata
        """

        metadata_resp = {
            "currency": "USD",
            "exchange_name": "NYSE",
            "first_trade_date": "1968-01-02",
            "instrument_type": "Equity",
            "symbol": "SPGI",
        }
        expected_resp = {
            "currency": "USD",
            "exchange_name": "NYSE",
            "first_trade_date": date(1968, 1, 2),
            "instrument_type": "Equity",
            "symbol": "SPGI",
        }
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/pricing/{SPGI_TRADING_ITEM_ID}/metadata",
            json=metadata_resp,
        )

        tool = GetHistoryMetadataFromIdentifier(kfinance_client=mock_client)
        resp = tool.run(ToolArgsWithIdentifier(identifier="SPGI").model_dump(mode="json"))
        assert resp == expected_resp


class TestGetInfoFromIdentifier:
    def test_get_info_from_identifier(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetInfoFromIdentifier tool
        WHEN request info for SPGI
        THEN we get back info for SPGI
        """

        # truncated from the original
        info_resp = {"name": "S&P Global Inc.", "status": "Operating"}
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/info/{SPGI_COMPANY_ID}",
            json=info_resp,
        )

        tool = GetInfoFromIdentifier(kfinance_client=mock_client)
        resp = tool.run(ToolArgsWithIdentifier(identifier="SPGI").model_dump(mode="json"))
        assert resp == str(info_resp)


class TestGetIsinFromTicker:
    def test_get_isin_from_ticker(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetIsinFromTicker tool
        WHEN we pass args with the SPGI ticker
        THEN we get back the SPGI isin
        """

        spgi_isin = "US78409V1044"
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/isin/{SPGI_SECURITY_ID}",
            json={"isin": spgi_isin},
        )

        tool = GetIsinFromTicker(kfinance_client=mock_client)
        resp = tool.run(GetIsinFromTickerArgs(ticker_str="SPGI").model_dump(mode="json"))
        assert resp == spgi_isin


class TestGetLatest:
    @time_machine.travel(datetime(2025, 1, 1, 12, tzinfo=datetime.now().astimezone().tzinfo))
    def test_get_latest(self, mock_client: Client):
        """
        GIVEN the GetLatest tool
        WHEN request latest info
        THEN we get back latest info
        """

        expected_resp = {
            "annual": {"latest_year": 2024},
            "now": {
                "current_date": "2025-01-01",
                "current_month": 1,
                "current_quarter": 1,
                "current_year": 2025,
            },
            "quarterly": {"latest_quarter": 4, "latest_year": 2024},
        }
        tool = GetLatest(kfinance_client=mock_client)
        resp = tool.run(GetLatestArgs().model_dump(mode="json"))
        assert resp == expected_resp


class TestGetNQuartersAgo:
    @time_machine.travel(datetime(2025, 1, 1, 12, tzinfo=datetime.now().astimezone().tzinfo))
    def test_get_n_quarters_ago(self, mock_client: Client):
        """
        GIVEN the GetNQuartersAgo tool
        WHEN we request 3 quarters ago
        THEN we get back 3 quarters ago
        """

        expected_resp = {"quarter": 2, "year": 2024}
        tool = GetNQuartersAgo(kfinance_client=mock_client)
        resp = tool.run(GetNQuartersAgoArgs(n=3).model_dump(mode="json"))
        assert resp == expected_resp


class TestPricesFromIdentifier:
    def test_get_prices_from_identifier(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetPricesFromIdentifier tool
        WHEN we request prices for SPGI
        THEN we get back prices for SPGI
        """

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/pricing/{SPGI_TRADING_ITEM_ID}/none/none/day/adjusted",
            # truncated response
            json={
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
            },
        )
        expected_response = "| date       |   open |   high |    low |   close |      volume |\n|:-----------|-------:|-------:|-------:|--------:|------------:|\n| 2024-04-11 | 424.26 | 425.99 | 422.04 |  422.92 | 1.12916e+06 |\n| 2024-04-12 | 419.23 | 421.94 | 416.45 |  417.81 | 1.18223e+06 |"

        tool = GetPricesFromIdentifier(kfinance_client=mock_client)
        response = tool.run(GetPricesFromIdentifierArgs(identifier="SPGI").model_dump(mode="json"))
        assert response == expected_response


class TestGetSecurityIdFromIdentifier:
    def test_get_security_id_from_identifier(self, mock_client: Client):
        """
        GIVEN the GetSecurityIdFromIdentifier tool
        WHEN we request the security id for SPGI
        THEN we get back the SPGI primary security id
        """
        tool = GetSecurityIdFromIdentifier(kfinance_client=mock_client)
        resp = tool.run(ToolArgsWithIdentifier(identifier="SPGI").model_dump(mode="json"))
        assert resp == SPGI_SECURITY_ID


class TestGetTradingItemIdFromIdentifier:
    def test_get_security_id_from_identifier(self, mock_client: Client):
        """
        GIVEN the GetTradingItemIdFromIdentifier tool
        WHEN we request the trading item id for SPGI
        THEN we get back the SPGI primary trading item id
        """
        tool = GetTradingItemIdFromIdentifier(kfinance_client=mock_client)
        resp = tool.run(ToolArgsWithIdentifier(identifier="SPGI").model_dump(mode="json"))
        assert resp == SPGI_TRADING_ITEM_ID
