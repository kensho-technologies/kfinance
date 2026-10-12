from datetime import datetime

import httpx2
import pytest
import time_machine

from kfinance.conftest import SPGI_ID_TRIPLE, optional_route
from kfinance.client.kfinance import Client
from kfinance.domains.earnings.earning_models import EarningsCallResp
from kfinance.domains.earnings.earning_tools import (
    GetEarningsFromIdentifiers,
    GetEarningsFromIdentifiersResp,
    GetTranscriptFromKeyDevIdResp,
    fetch_earnings_from_company_id,
    get_earnings_from_identifiers,
    get_transcript_from_key_dev_id,
)


class TestEarnings:
    @pytest.fixture
    def add_spgi_earnings_mock_resp(self, httpx2_mock) -> None:
        """Add mock response for SPGI earnings."""
        optional_route(
            httpx2_mock.get(
                f"https://kfinance.kensho.com/api/v1/earnings/{SPGI_ID_TRIPLE.company_id}"
            )
        ).respond(
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
            }
        )
        # private company without earnings
        optional_route(httpx2_mock.get("https://kfinance.kensho.com/api/v1/earnings/1")).respond(
            json={"earnings": []}
        )

    @pytest.mark.asyncio
    async def test_fetch_earnings_from_company_id(
        self,
        httpx_client: httpx2.AsyncClient,
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
        httpx_client: httpx2.AsyncClient,
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
            identifier_info={"SPGI": SPGI_ID_TRIPLE},
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
        httpx_client: httpx2.AsyncClient,
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
        httpx_client: httpx2.AsyncClient,
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


    @time_machine.travel(datetime(2025, 4, 1))
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "earnings_timeframe, expected_key_dev_ids",
        [
            pytest.param("all", [12345, 12346], id="all"),
            pytest.param("latest", [12345], id="latest"),
            pytest.param("next", [12346], id="next"),
        ],
    )
    async def test_earnings_timeframe_picks_which_calls_the_tool_returns(
        self,
        mock_client: Client,
        httpx_client: httpx2.AsyncClient,
        add_spgi_earnings_mock_resp: None,
        earnings_timeframe: str,
        expected_key_dev_ids: list[int],
    ) -> None:
        """
        GIVEN SPGI's Q4 2024 call (past) and Q1 2025 call (upcoming) on 2025-04-01
        WHEN the tool runs with each earnings_timeframe
        THEN all returns both calls, latest only the past one, and next only the upcoming one
        """
        tool = GetEarningsFromIdentifiers(kfinance_client=mock_client)

        resp = await tool.arun_without_langchain(
            identifiers=["SPGI"], earnings_timeframe=earnings_timeframe
        )

        result = resp["results"]["SPGI"]["data"]
        calls = result["earnings_calls"] if earnings_timeframe == "all" else [result]
        assert sorted(call["key_dev_id"] for call in calls) == expected_key_dev_ids

    @time_machine.travel(datetime(2025, 5, 1))
    @pytest.mark.asyncio
    async def test_next_earnings_reports_an_error_when_none_is_scheduled(
        self,
        mock_client: Client,
        httpx_client: httpx2.AsyncClient,
        add_spgi_earnings_mock_resp: None,
    ) -> None:
        """
        GIVEN SPGI's calls are both in the past on 2025-05-01
        WHEN the tool runs with earnings_timeframe next
        THEN there is no result for SPGI, and an error says so
        """
        tool = GetEarningsFromIdentifiers(kfinance_client=mock_client)

        resp = await tool.arun_without_langchain(identifiers=["SPGI"], earnings_timeframe="next")

        assert resp["results"] == {}
        assert "No next earnings available for SPGI." in resp["errors"]


class TestTranscript:
    @pytest.fixture
    def add_transcript_mock_resp(self, httpx2_mock) -> None:
        """Add mock response for transcript."""
        optional_route(
            httpx2_mock.get("https://kfinance.kensho.com/api/v1/transcript/12345")
        ).respond(
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
            }
        )

    @pytest.mark.asyncio
    async def test_get_transcript_from_key_dev_id(
        self,
        httpx_client: httpx2.AsyncClient,
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
