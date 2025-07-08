import contextlib
from contextlib import nullcontext as does_not_raise

from pydantic import BaseModel, ValidationError
import pytest
from pytest import raises
from requests_mock import Mocker
import time_machine

from kfinance.kfinance import Client, NoEarningsDataError
from kfinance.models.competitor_models import CompetitorSource
from kfinance.models.segment_models import SegmentType
from kfinance.tests.conftest import SPGI_COMPANY_ID
from kfinance.tests.test_objects import MOCK_COMPANY_DB, MOCK_MERGERS_DB, ordered
from kfinance.tool_calling import (
    GetCompetitorsFromIdentifiers,
    GetEarningsFromIdentifiers,
    GetInfoFromIdentifier,
    GetLatestEarnings,
    GetNextEarnings,
    GetTranscript, GetInfoFromIdentifiers,
)
from kfinance.tool_calling.get_advisors_for_company_in_transaction_from_identifier import (
    GetAdvisorsForCompanyInTransactionFromIdentifiers,
    GetAdvisorsForCompanyInTransactionFromIdentifierArgs,
)
from kfinance.tool_calling.get_competitors_from_identifiers import GetCompetitorsFromIdentifiersArgs
from kfinance.tool_calling.get_merger_info_from_transaction_id import (
    GetMergerInfoFromTransactionId,
    GetMergerInfoFromTransactionIdArgs,
)
from kfinance.tool_calling.get_mergers_from_identifier import GetMergersFromIdentifier
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

        tool = GetEarningsFromIdentifiers(kfinance_client=mock_client)
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



class TestGetEndpointsFromToolCallsWithGrounding:
    def test_get_info_from_identifier_with_grounding(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN a KfinanceTool tool
        WHEN we run the tool with `run_with_grounding`
        THEN we get back endpoint urls in addition to the usual tool response.
        """

        # truncated from the original
        resp_data = "{'name': 'S&P Global Inc.', 'status': 'Operating'}"
        resp_endpoint = [
            "https://kfinance.kensho.com/api/v1/id/SPGI",
            "https://kfinance.kensho.com/api/v1/info/21719",
        ]
        expected_resp = {"data": resp_data, "endpoint_urls": resp_endpoint}

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/info/{SPGI_COMPANY_ID}",
            json=resp_data,
        )

        tool = GetInfoFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run_with_grounding(identifiers=["SPGI"])
        assert resp == expected_resp


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
