from datetime import datetime

from requests_mock import Mocker
import time_machine

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_COMPANY_ID
from kfinance.domains.earnings.earning_tools import (
    GetEarningsFromIdentifiers,
    GetLatestEarningsFromIdentifiers,
    GetNextEarningsFromIdentifiers,
    GetTranscriptFromKeyDevId,
    GetTranscriptFromKeyDevIdArgs,
)
from kfinance.integrations.tool_calling.tool_calling_models import ToolArgsWithIdentifiers


class TestGetEarnings:
    earnings_response = {
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

    def test_get_earnings_from_identifiers(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetEarnings tool
        WHEN we request all earnings for SPGI
        THEN we get back all SPGI earnings
        """

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/earnings/{SPGI_COMPANY_ID}",
            json=self.earnings_response,
        )

        expected_response = {
            "SPGI": [
                {
                    "datetime": "2025-04-29T12:30:00Z",
                    "key_dev_id": 12346,
                    "name": "SPGI Q1 2025 Earnings Call",
                },
                {
                    "datetime": "2025-02-11T13:30:00Z",
                    "key_dev_id": 12345,
                    "name": "SPGI Q4 2024 Earnings Call",
                },
            ]
        }

        tool = GetEarningsFromIdentifiers(kfinance_client=mock_client)
        response = tool.run(ToolArgsWithIdentifiers(identifiers=["SPGI"]).model_dump(mode="json"))
        assert response == expected_response

    @time_machine.travel(
        datetime(
            2025,
            5,
            1,
        )
    )
    def test_get_latest_earnings_from_identifiers(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetLatestEarnings tool
        WHEN we request the latest earnings for SPGI
        THEN we get back the latest SPGI earnings
        """

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/earnings/{SPGI_COMPANY_ID}",
            json=self.earnings_response,
        )

        expected_response = {
            "SPGI": {
                "datetime": "2025-04-29T12:30:00Z",
                "key_dev_id": 12346,
                "name": "SPGI Q1 2025 Earnings Call",
            }
        }

        tool = GetLatestEarningsFromIdentifiers(kfinance_client=mock_client)
        response = tool.run(ToolArgsWithIdentifiers(identifiers=["SPGI"]).model_dump(mode="json"))
        assert response == expected_response

    def test_get_latest_earnings_no_data(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetLatestEarnings tool
        WHEN we request the latest earnings for a company with no data
        THEN we get a `No latest earnings available` message.
        """
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/earnings/{SPGI_COMPANY_ID}",
            json={"earnings": []},
        )
        expected_response = {"SPGI": "No latest earnings available."}

        tool = GetLatestEarningsFromIdentifiers(kfinance_client=mock_client)
        response = tool.run(ToolArgsWithIdentifiers(identifiers=["SPGI"]).model_dump(mode="json"))
        assert response == expected_response

    @time_machine.travel(
        datetime(
            2025,
            4,
            1,
        )
    )
    def test_get_next_earnings(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetNextEarningsFromIdentifiers tool
        WHEN we request the next earnings for SPGI
        THEN we get back the next SPGI earnings
        """

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/earnings/{SPGI_COMPANY_ID}",
            json=self.earnings_response,
        )

        expected_response = {
            "SPGI": {
                "datetime": "2025-04-29T12:30:00Z",
                "key_dev_id": 12346,
                "name": "SPGI Q1 2025 Earnings Call",
            }
        }

        tool = GetNextEarningsFromIdentifiers(kfinance_client=mock_client)
        response = tool.run(ToolArgsWithIdentifiers(identifiers=["SPGI"]).model_dump(mode="json"))
        assert response == expected_response

    def test_get_next_earnings_no_data(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetNextEarnings tool
        WHEN we request the next earnings for a company with no data
        THEN we get a `No next earnings available` message.
        """
        earnings_data = {"earnings": []}

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/earnings/{SPGI_COMPANY_ID}",
            json=earnings_data,
        )
        expected_response = {"SPGI": "No next earnings available."}

        tool = GetNextEarningsFromIdentifiers(kfinance_client=mock_client)
        response = tool.run(ToolArgsWithIdentifiers(identifiers=["SPGI"]).model_dump(mode="json"))
        assert response == expected_response


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

        tool = GetTranscriptFromKeyDevId(kfinance_client=mock_client)
        response = tool.run(GetTranscriptFromKeyDevIdArgs(key_dev_id=12345).model_dump(mode="json"))
        assert response == expected_response
