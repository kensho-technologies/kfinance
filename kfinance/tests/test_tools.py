import contextlib
from contextlib import nullcontext as does_not_raise
from datetime import date, datetime

from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import BaseModel, ValidationError
import pytest
from pytest import raises
from requests_mock import Mocker
import time_machine

from kfinance.constants import (
    BusinessRelationshipType,
    Capitalization,
    CompetitorSource,
    SegmentType,
    StatementType,
)
from kfinance.kfinance import Client, NoEarningsDataError
from kfinance.tests.conftest import SPGI_COMPANY_ID, SPGI_SECURITY_ID, SPGI_TRADING_ITEM_ID
from kfinance.tests.test_objects import MOCK_COMPANY_DB, MOCK_MERGERS_DB, ordered
from kfinance.tool_calling import (
    GetCompetitorsFromIdentifier,
    GetEarnings,
    GetFinancialLineItemFromIdentifier,
    GetFinancialStatementFromIdentifier,
    GetHistoryMetadataFromIdentifier,
    GetInfoFromIdentifier,
    GetIsinFromTicker,
    GetLatest,
    GetLatestEarnings,
    GetNextEarnings,
    GetNQuartersAgo,
    GetPricesFromIdentifier,
    GetTranscript,
    ResolveIdentifier,
)
from kfinance.tool_calling.get_advisors_for_company_in_transaction_from_identifier import (
    GetAdvisorsForCompanyInTransactionFromIdentifier,
    GetAdvisorsForCompanyInTransactionFromIdentifierArgs,
)
from kfinance.tool_calling.get_business_relationship_from_identifier import (
    GetBusinessRelationshipFromIdentifier,
    GetBusinessRelationshipFromIdentifierArgs,
)
from kfinance.tool_calling.get_capitalization_from_identifier import (
    GetCapitalizationFromIdentifier,
    GetCapitalizationFromIdentifierArgs,
)
from kfinance.tool_calling.get_competitors_from_identifier import (
    GetCompetitorsFromIdentifierArgs,
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
from kfinance.tool_calling.get_merger_info_from_transaction_id import (
    GetMergerInfoFromTransactionId,
    GetMergerInfoFromTransactionIdArgs,
)
from kfinance.tool_calling.get_mergers_from_identifier import GetMergersFromIdentifier
from kfinance.tool_calling.get_n_quarters_ago import GetNQuartersAgoArgs
from kfinance.tool_calling.get_prices_from_identifier import GetPricesFromIdentifierArgs
from kfinance.tool_calling.get_segments_from_identifier import (
    GetSegmentsFromIdentifier,
    GetSegmentsFromIdentifierArgs,
)
from kfinance.tool_calling.get_transcript import GetTranscriptArgs
from kfinance.tool_calling.shared_models import ToolArgsWithIdentifier, ValidQuarter


class TestGetCompaniesAdvisingCompanyInTransactionFromIdentifier:
    def test_get_companies_advising_company_in_transaction_from_identifier(
        self, requests_mock: Mocker, mock_client: Client
    ):
        expected_response = {
            "advisors": [
                {
                    "advisor_company_id": 251994106,
                    "advisor_company_name": "Kensho Technologies, Inc.",
                    "advisor_type_name": "Professional Mongo Enjoyer",
                }
            ]
        }
        transaction_id = 517414
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/merger/info/{transaction_id}/advisors/21835",
            json=expected_response,
        )
        tool = GetAdvisorsForCompanyInTransactionFromIdentifier(kfinance_client=mock_client)
        args = GetAdvisorsForCompanyInTransactionFromIdentifierArgs(
            identifier="MSFT", transaction_id=transaction_id
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response["advisors"]


class TestGetMergerInfoFromTransactionId:
    def test_get_merger_info_from_transaction_id(self, requests_mock: Mocker, mock_client: Client):
        expected_response = MOCK_MERGERS_DB["517414"]
        transaction_id = 517414
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/merger/info/{transaction_id}",
            json=expected_response,
        )
        tool = GetMergerInfoFromTransactionId(kfinance_client=mock_client)
        args = GetMergerInfoFromTransactionIdArgs(transaction_id=transaction_id)
        response = tool.run(args.model_dump(mode="json"))
        assert ordered(response) == ordered(expected_response)


class TestGetMergersFromIdentifier:
    def test_get_mergers_from_identifier(self, requests_mock: Mocker, mock_client: Client):
        expected_response = MOCK_COMPANY_DB["21835"]["mergers"]
        company_id = 21835
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/mergers/{company_id}", json=expected_response
        )
        tool = GetMergersFromIdentifier(kfinance_client=mock_client)
        args = ToolArgsWithIdentifier(identifier="MSFT")
        response = tool.run(args.model_dump(mode="json"))
        assert ordered(response) == ordered(expected_response)


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


class TestGetSegmentsFromIdentifier:
    def test_get_segments_from_identifier(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetSegmentsFromIdentifier tool
        WHEN we request the SPGI business segment
        THEN we get back the SPGI business segment
        """

        segments_response = {
            "segments": {
                "2020": {
                    "Commodity Insights": {
                        "CAPEX": -7000000.0,
                        "D&A": 17000000.0,
                    },
                    "Unallocated Assets Held for Sale": None,
                },
                "2021": {
                    "Commodity Insights": {
                        "CAPEX": -2000000.0,
                        "D&A": 12000000.0,
                    },
                    "Unallocated Assets Held for Sale": {"Total Assets": 321000000.0},
                },
            },
        }
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/segments/{SPGI_COMPANY_ID}/business/none/none/none/none/none",
            # truncated from the original API response
            json=segments_response,
        )

        tool = GetSegmentsFromIdentifier(kfinance_client=mock_client)
        args = GetSegmentsFromIdentifierArgs(identifier="SPGI", segment_type=SegmentType.business)
        response = tool.run(args.model_dump(mode="json"))
        assert response == segments_response["segments"]


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


class TestResolveIdentifier:
    def test_resolve_identifier(self, mock_client: Client):
        """
        GIVEN the ResolveIdentifier tool
        WHEN request to resolve SPGI
        THEN we get back a dict with the SPGI company id, security id, and trading item id
        """
        tool = ResolveIdentifier(kfinance_client=mock_client)
        resp = tool.run(ToolArgsWithIdentifier(identifier="SPGI").model_dump(mode="json"))
        assert resp == {
            "company_id": SPGI_COMPANY_ID,
            "security_id": SPGI_SECURITY_ID,
            "trading_item_id": SPGI_TRADING_ITEM_ID,
        }


class TestGetLatestEarnings:
    def test_get_latest_earnings(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetLatestEarnings tool
        WHEN we request the latest earnings for SPGI
        THEN we get back the latest SPGI earnings
        """
        earnings_data = {
            "earnings": [
                {
                    "name": "SPGI Q4 2024 Earnings Call",
                    "datetime": "2025-02-11T13:30:00Z",
                    "keydevid": 12345,
                },
                {
                    "name": "SPGI Q3 2024 Earnings Call",
                    "datetime": "2024-10-30T12:30:00Z",
                    "keydevid": 12344,
                },
            ]
        }

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/earnings/{SPGI_COMPANY_ID}",
            json=earnings_data,
        )

        expected_response = {
            "name": "SPGI Q4 2024 Earnings Call",
            "key_dev_id": 12345,
            "datetime": "2025-02-11T13:30:00+00:00",
        }

        tool = GetLatestEarnings(kfinance_client=mock_client)
        response = tool.run(ToolArgsWithIdentifier(identifier="SPGI").model_dump(mode="json"))
        assert response == expected_response

    def test_get_latest_earnings_no_data(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetLatestEarnings tool
        WHEN we request the latest earnings for a company with no data
        THEN we get a NoEarningsDataError exception
        """
        earnings_data = {"earnings": []}

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/earnings/{SPGI_COMPANY_ID}",
            json=earnings_data,
        )

        tool = GetLatestEarnings(kfinance_client=mock_client)
        with raises(NoEarningsDataError, match="Latest earnings for SPGI not found"):
            tool.run(ToolArgsWithIdentifier(identifier="SPGI").model_dump(mode="json"))


class TestGetNextEarnings:
    def test_get_next_earnings_(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetNextEarnings tool
        WHEN we request the next earnings for SPGI
        THEN we get back the next SPGI earnings
        """
        earnings_data = {
            "earnings": [
                {
                    "name": "SPGI Q1 2025 Earnings Call",
                    "datetime": "2025-04-29T12:30:00Z",
                    "keydevid": 12346,
                },
                {
                    "name": "SPGI Q4 2024 Earnings Call",
                    "datetime": "2025-02-11T13:30:00Z",
                    "keydevid": 12345,
                },
            ]
        }

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/earnings/{SPGI_COMPANY_ID}",
            json=earnings_data,
        )

        expected_response = {
            "name": "SPGI Q1 2025 Earnings Call",
            "key_dev_id": 12346,
            "datetime": "2025-04-29T12:30:00+00:00",
        }

        with time_machine.travel("2025-03-01T00:00:00+00:00"):
            tool = GetNextEarnings(kfinance_client=mock_client)
            response = tool.run(ToolArgsWithIdentifier(identifier="SPGI").model_dump(mode="json"))
            assert response == expected_response

    def test_get_next_earnings_no_data(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetNextEarnings tool
        WHEN we request the next earnings for a company with no data
        THEN we get a NoEarningsDataError exception
        """
        earnings_data = {"earnings": []}

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/earnings/{SPGI_COMPANY_ID}",
            json=earnings_data,
        )

        with time_machine.travel("2025-03-01T00:00:00+00:00"):
            tool = GetNextEarnings(kfinance_client=mock_client)
            with raises(NoEarningsDataError, match="Next earnings for SPGI not found"):
                tool.run(ToolArgsWithIdentifier(identifier="SPGI").model_dump(mode="json"))


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
                    "keydevid": 12346,
                },
                {
                    "name": "SPGI Q4 2024 Earnings Call",
                    "datetime": "2025-02-11T13:30:00Z",
                    "keydevid": 12345,
                },
            ]
        }

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/earnings/{SPGI_COMPANY_ID}",
            json=earnings_data,
        )

        expected_response = [
            {
                "name": "SPGI Q1 2025 Earnings Call",
                "key_dev_id": 12346,
                "datetime": "2025-04-29T12:30:00+00:00",
            },
            {
                "name": "SPGI Q4 2024 Earnings Call",
                "key_dev_id": 12345,
                "datetime": "2025-02-11T13:30:00+00:00",
            },
        ]

        tool = GetEarnings(kfinance_client=mock_client)
        response = tool.run(ToolArgsWithIdentifier(identifier="SPGI").model_dump(mode="json"))
        assert response == expected_response

    def test_get_earnings_no_data(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetEarnings tool
        WHEN we request all earnings for a company with no data
        THEN we get a NoEarningslDataError exception
        """
        earnings_data = {"earnings": []}

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/earnings/{SPGI_COMPANY_ID}",
            json=earnings_data,
        )

        tool = GetEarnings(kfinance_client=mock_client)
        with raises(NoEarningsDataError, match="Earnings for SPGI not found"):
            tool.run(ToolArgsWithIdentifier(identifier="SPGI").model_dump(mode="json"))


class TestGetTranscript:
    def test_get_transcript(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetTranscript tool
        WHEN we request a transcript by key_dev_id
        THEN we get back the transcript text
        """
        transcript_data = {
            "transcript": [
                {
                    "person_name": "Operator",
                    "text": "Good morning, everyone.",
                    "component_type": "speech",
                },
                {
                    "person_name": "CEO",
                    "text": "Thank you for joining us today.",
                    "component_type": "speech",
                },
            ]
        }

        requests_mock.get(
            url="https://kfinance.kensho.com/api/v1/transcript/12345",
            json=transcript_data,
        )

        expected_response = (
            "Operator: Good morning, everyone.\n\nCEO: Thank you for joining us today."
        )

        tool = GetTranscript(kfinance_client=mock_client)
        response = tool.run(GetTranscriptArgs(key_dev_id=12345).model_dump(mode="json"))
        assert response == expected_response


class TestGetCompetitorsFromIdentifier:
    def test_get_competitors_from_identifier(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetCompetitorsFromIdentifier tool
        WHEN we request the SPGI competitors that are named by competitors
        THEN we get back the SPGI competitors that are named by competitors
        """
        expected_competitors_response = {
            "companies": [
                {"company_id": 35352, "company_name": "The Descartes Systems Group Inc."},
                {"company_id": 4003514, "company_name": "London Stock Exchange Group plc"},
            ]
        }
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/competitors/{SPGI_COMPANY_ID}/named_by_competitor",
            # truncated from the original API response
            json=expected_competitors_response,
        )

        tool = GetCompetitorsFromIdentifier(kfinance_client=mock_client)
        args = GetCompetitorsFromIdentifierArgs(
            identifier="SPGI", competitor_source=CompetitorSource.named_by_competitor
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_competitors_response


class TestValidQuarter:
    class QuarterModel(BaseModel):
        quarter: ValidQuarter | None

    @pytest.mark.parametrize(
        "input_quarter, expectation, expected_quarter",
        [
            pytest.param(1, does_not_raise(), 1, id="int input works"),
            pytest.param("1", does_not_raise(), 1, id="str input works"),
            pytest.param(None, does_not_raise(), None, id="None input works"),
            pytest.param(5, pytest.raises(ValidationError), None, id="invalid int raises"),
            pytest.param("5", pytest.raises(ValidationError), None, id="invalid str raises"),
        ],
    )
    def test_valid_quarter(
        self,
        input_quarter: int | str | None,
        expectation: contextlib.AbstractContextManager,
        expected_quarter: int | None,
    ) -> None:
        """
        GIVEN a model that uses `ValidQuarter`
        WHEN we deserialize with int, str, or None
        THEN valid str get coerced to int. Invalid values raise.
        """
        with expectation:
            res = self.QuarterModel.model_validate(dict(quarter=input_quarter))
            assert res.quarter == expected_quarter
