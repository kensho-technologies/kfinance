from datetime import date

from langchain_core.utils.function_calling import convert_to_openai_tool
from requests_mock import Mocker

from kfinance.constants import Capitalization, StatementType
from kfinance.kfinance import Client
from kfinance.tests.conftest import SPGI_COMPANY_ID, SPGI_SECURITY_ID, SPGI_TRADING_ITEM_ID
from kfinance.tool_calling import (
    GetCapitalizationFromCompanyId,
    GetCusipFromSecurityId,
    GetEarningsCallDatetimesFromCompanyId,
    GetFinancialStatementFromCompanyId,
    GetHistoryMetadataFromTradingItemId,
    GetInfoFromCompanyId,
    GetIsinFromSecurityId,
    GetPricesFromTradingItemId,
    ResolveIdentifier,
)
from kfinance.tool_calling.individual_tools.get_capitalization_from_company_id import (
    GetCapitalizationFromCompanyIdArgs,
)
from kfinance.tool_calling.individual_tools.get_cusip_from_security_id import (
    GetCusipFromSecurityIdArgs,
)
from kfinance.tool_calling.individual_tools.get_earnings_call_datetimes_from_company_id import (
    GetEarningsCallDatetimesFromCompanyIdArgs,
)
from kfinance.tool_calling.individual_tools.get_financial_line_item_from_company_id import (
    GetFinancialLineItemFromCompanyId,
    GetFinancialLineItemFromCompanyIdArgs,
)
from kfinance.tool_calling.individual_tools.get_financial_statement_from_company_id import (
    GetFinancialStatementFromCompanyIdArgs,
)
from kfinance.tool_calling.individual_tools.get_history_metadata_from_trading_item_id import (
    GetHistoryMetadataFromTradingItemIdArgs,
)
from kfinance.tool_calling.individual_tools.get_info_from_company_id import GetInfoFromCompanyIdArgs
from kfinance.tool_calling.individual_tools.get_isin_from_security_id import (
    GetIsinFromSecurityIdArgs,
)
from kfinance.tool_calling.individual_tools.get_prices_from_trading_item_id import (
    GetPricesFromTradingItemIdArgs,
)
from kfinance.tool_calling.individual_tools.resolve_identifier import ResolveIdentifierArgs


class TestGetCapitalizationFromCompanyId:
    def test_get_capitalization_from_company_id(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetCapitalizationFromCompanyId tool
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

        tool = GetCapitalizationFromCompanyId(kfinance_client=mock_client)
        args = GetCapitalizationFromCompanyIdArgs(
            company_id=SPGI_COMPANY_ID, capitalization=Capitalization.market_cap
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response


class TestGetCusipFromSecurityId:
    def test_get_cusip_from_security_id(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetCusipFromSecurityId tool
        WHEN we pass args with the SPGI security id
        THEN we get back the SPGI cusip
        """

        spgi_cusip = "78409V104"
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/cusip/{SPGI_SECURITY_ID}",
            json={"cusip": spgi_cusip},
        )
        tool = GetCusipFromSecurityId(kfinance_client=mock_client)
        resp = tool.run(
            GetCusipFromSecurityIdArgs(security_id=SPGI_SECURITY_ID).model_dump(mode="json")
        )
        assert resp == spgi_cusip


class TestGetEarningsCallDatetimesFromCompanyId:
    def test_get_earnings_call_datetimes_from_company_id(
        self, requests_mock: Mocker, mock_client: Client
    ):
        """
        GIVEN the GetEarningsCallDatetimesFromCompanyId tool
        WHEN we request earnings call datetimes for SPGI
        THEN we get back the expected SPGI earnings call datetimes
        """

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/earnings/{SPGI_COMPANY_ID}/dates",
            json={"earnings": ["2025-04-29T12:30:00", "2025-02-11T13:30:00"]},
        )
        expected_response = '["2025-04-29T12:30:00+00:00", "2025-02-11T13:30:00+00:00"]'

        tool = GetEarningsCallDatetimesFromCompanyId(kfinance_client=mock_client)
        response = tool.run(
            GetEarningsCallDatetimesFromCompanyIdArgs(company_id=SPGI_COMPANY_ID).model_dump(
                mode="json"
            )
        )
        assert response == expected_response


class TestGetFinancialLineItemFromCompanyId:
    def test_get_financial_line_item_from_company_id(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN the GetFinancialLineItemFromCompanyId tool
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

        tool = GetFinancialLineItemFromCompanyId(kfinance_client=mock_client)
        args = GetFinancialLineItemFromCompanyIdArgs(
            company_id=SPGI_COMPANY_ID, line_item="revenue"
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_line_items_and_aliases_included_in_schema(self, mock_client: Client):
        """
        GIVEN a GetFinancialLineItemFromCompanyId tool
        WHEN we generate an openai schema from the tool
        THEN all line items and aliases are included in the line item enum
        """
        tool = GetFinancialLineItemFromCompanyId(kfinance_client=mock_client)
        oai_schema = convert_to_openai_tool(tool)
        line_items = oai_schema["function"]["parameters"]["properties"]["line_item"]["enum"]
        # revenue is a line item
        assert "revenue" in line_items
        # normal_revenue is an alias for revenue
        assert "normal_revenue" in line_items


class TestGetFinancialStatementFromCompanyId:
    def test_get_financial_statement_from_company_id(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN the GetFinancialLineItemFromCompanyId tool
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

        tool = GetFinancialStatementFromCompanyId(kfinance_client=mock_client)
        args = GetFinancialStatementFromCompanyIdArgs(
            company_id=SPGI_COMPANY_ID, statement=StatementType.income_statement
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response


class TestGetHistoryMetadataFromTradingItemId:
    def test_get_history_metadata_from_trading_item_id(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN the GetHistoryMetadataFromTradingItemId tool
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

        tool = GetHistoryMetadataFromTradingItemId(kfinance_client=mock_client)
        resp = tool.run(
            GetHistoryMetadataFromTradingItemIdArgs(
                trading_item_id=SPGI_TRADING_ITEM_ID
            ).model_dump(mode="json")
        )
        assert resp == expected_resp


class TestGetInfoFromCompanyId:
    def test_get_info_from_company_id(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetInfoFromCompanyId tool
        WHEN request info for SPGI
        THEN we get back info for SPGI
        """

        # truncated from the original
        info_resp = {"name": "S&P Global Inc.", "status": "Operating"}
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/info/{SPGI_COMPANY_ID}",
            json=info_resp,
        )

        tool = GetInfoFromCompanyId(kfinance_client=mock_client)
        resp = tool.run(
            GetInfoFromCompanyIdArgs(company_id=SPGI_COMPANY_ID).model_dump(mode="json")
        )
        assert resp == str(info_resp)


class TestGetIsinFromSecurityId:
    def test_get_isin_from_security_id(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetIsinFromSecurityId tool
        WHEN we pass args with the SPGI security id
        THEN we get back the SPGI isin
        """

        spgi_isin = "US78409V1044"
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/isin/{SPGI_SECURITY_ID}",
            json={"isin": spgi_isin},
        )

        tool = GetIsinFromSecurityId(kfinance_client=mock_client)
        resp = tool.run(
            GetIsinFromSecurityIdArgs(security_id=SPGI_SECURITY_ID).model_dump(mode="json")
        )
        assert resp == spgi_isin


class TestPricesFromTradingItemId:
    def test_get_prices_from_trading_item_id(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetPricesFromTradingItemId tool
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

        tool = GetPricesFromTradingItemId(kfinance_client=mock_client)
        response = tool.run(
            GetPricesFromTradingItemIdArgs(trading_item_id=SPGI_TRADING_ITEM_ID).model_dump(
                mode="json"
            )
        )
        assert response == expected_response


class TestResolveIdentifier:
    def test_resolve_identifier(self, mock_client: Client):
        """
        GIVEN the ResolveIdentifier tool
        WHEN request to resolve SPGI
        THEN we get back a dict with the SPGI company id, security id, and trading item id
        """
        tool = ResolveIdentifier(kfinance_client=mock_client)
        resp = tool.run(ResolveIdentifierArgs(identifier="SPGI").model_dump(mode="json"))
        assert resp == {
            "company_id": SPGI_COMPANY_ID,
            "security_id": SPGI_SECURITY_ID,
            "trading_item_id": SPGI_TRADING_ITEM_ID,
        }
