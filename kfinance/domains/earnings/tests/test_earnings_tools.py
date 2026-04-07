from datetime import datetime

import httpx
import pytest
from pytest_httpx import HTTPXMock
import time_machine

from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.earnings.earning_models import EarningsCallResp
from kfinance.domains.earnings.earning_tools import (
    GetEarningsFromIdentifiersResp,
    GetTranscriptFromKeyDevIdResp,
    fetch_earnings_from_company_id,
    get_earnings_from_identifiers,
    get_transcript_from_key_dev_id,
)


class TestEarnings:
    @pytest.fixture
    def add_spgi_earnings_mock_resp(self, httpx_mock: HTTPXMock) -> None:
        """Add mock response for SPGI earnings."""
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/earnings/{SPGI_ID_TRIPLE.company_id}",
            json={
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
            },
            is_optional=True,
        )
        # private company without earnings
        httpx_mock.add_response(
            method="GET",
            url="https://kfinance.kensho.com/api/v1/earnings/1",
            json={"earnings": []},
            is_optional=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_earnings_from_company_id(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_earnings_mock_resp: None,
    ) -> None:
        """
        WHEN we request SPGI's earnings (using SPGI's company id)
        THEN we get back SPGI's earnings
        """

        resp = await fetch_earnings_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            httpx_client=httpx_client,
        )

        expected_resp = EarningsCallResp.model_validate(
            {
                "earnings": [
                    {
                        "name": "SPGI Q1 2025 Earnings Call",
                        "key_dev_id": 12346,
                        "datetime": "2025-04-29T12:30:00Z",
                    },
                    {
                        "name": "SPGI Q4 2024 Earnings Call",
                        "key_dev_id": 12345,
                        "datetime": "2025-02-11T13:30:00Z",
                    },
                ]
            }
        )
        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_earnings_from_identifiers(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_earnings_mock_resp: None,
    ) -> None:
        """
        WHEN we request all earnings for SPGI and a non-existent company
        THEN we get back all SPGI earnings and an error for the non-existent company
        """

        expected_resp = GetEarningsFromIdentifiersResp(
            identifier_results={
                "SPGI": EarningsCallResp.model_validate(
                    {
                        "earnings": [
                            {
                                "name": "SPGI Q1 2025 Earnings Call",
                                "key_dev_id": 12346,
                                "datetime": "2025-04-29T12:30:00Z",
                            },
                            {
                                "name": "SPGI Q4 2024 Earnings Call",
                                "key_dev_id": 12345,
                                "datetime": "2025-02-11T13:30:00Z",
                            },
                        ]
                    }
                )
            },
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )

        resp = await get_earnings_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            httpx_client=httpx_client,
        )

        assert resp == expected_resp

    @time_machine.travel(datetime(2025, 5, 1))
    @pytest.mark.asyncio
    async def test_get_latest_earnings_logic(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_earnings_mock_resp: None,
    ) -> None:
        """
        WHEN we request the latest earnings for SPGI and a private company without earnings
        THEN we get back the latest SPGI earnings and an error for the private company
        """

        resp = await get_earnings_from_identifiers(
            identifiers=["SPGI", "private_company"],
            httpx_client=httpx_client,
        )

        # Verify SPGI latest earnings logic
        spgi_earnings = resp.identifier_results["SPGI"]
        latest_earnings = spgi_earnings.most_recent_earnings
        assert latest_earnings is not None
        assert latest_earnings.name == "SPGI Q1 2025 Earnings Call"
        assert latest_earnings.key_dev_id == 12346

    @time_machine.travel(datetime(2025, 4, 1))
    @pytest.mark.asyncio
    async def test_get_next_earnings_logic(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_earnings_mock_resp: None,
    ) -> None:
        """
        WHEN we request the next earnings for SPGI and a private company
        THEN we get back the next SPGI earnings and an error for the private company
        """

        resp = await get_earnings_from_identifiers(
            identifiers=["SPGI", "private_company"],
            httpx_client=httpx_client,
        )

        # Verify SPGI next earnings logic
        spgi_earnings = resp.identifier_results["SPGI"]
        next_earnings = spgi_earnings.next_earnings
        assert next_earnings is not None
        assert next_earnings.name == "SPGI Q1 2025 Earnings Call"
        assert next_earnings.key_dev_id == 12346


class TestTranscript:
    @pytest.fixture
    def add_transcript_mock_resp(self, httpx_mock: HTTPXMock) -> None:
        """Add mock response for transcript."""
        httpx_mock.add_response(
            method="GET",
            url="https://kfinance.kensho.com/api/v1/transcript/12345",
            json={
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
            },
            is_optional=True,
        )

    @pytest.mark.asyncio
    async def test_get_transcript_from_key_dev_id(
        self,
        httpx_client: httpx.AsyncClient,
        add_transcript_mock_resp: None,
    ) -> None:
        """
        WHEN we request a transcript by key_dev_id
        THEN we get back the transcript text
        """

        resp = await get_transcript_from_key_dev_id(
            key_dev_id=12345,
            httpx_client=httpx_client,
        )

        expected_response = GetTranscriptFromKeyDevIdResp(
            transcript="Operator: Good morning, everyone.\n\nCEO: Thank you for joining us today."
        )
        assert resp == expected_response
