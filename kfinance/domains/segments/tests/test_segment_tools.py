import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX
from kfinance.domains.segments.segment_models import SegmentsResp, SegmentType
from kfinance.domains.segments.segment_tools import (
    GetSegmentsFromIdentifiersResp,
    fetch_segments_from_company_ids,
    get_segments_from_identifiers,
)


class TestSegments:
    segments_response = {
        "currency": "USD",
        "periods": {
            "CY2020": {
                "period_end_date": "2020-12-31",
                "num_months": 12,
                "segments": [
                    {
                        "name": "Commodity Insights",
                        "line_items": [
                            {"name": "CAPEX", "value": "-7000000.0", "sources": []},
                            {"name": "D&A", "value": "17000000.0", "sources": []},
                        ],
                    }
                ],
            },
            "CY2021": {
                "period_end_date": "2021-12-31",
                "num_months": 12,
                "segments": [
                    {
                        "name": "Commodity Insights",
                        "line_items": [
                            {"name": "CAPEX", "value": "-2000000.0", "sources": []},
                            {"name": "D&A", "value": "12000000.0", "sources": []},
                        ],
                    },
                    {
                        "name": "Unallocated Assets Held for Sale",
                        "line_items": [
                            {"name": "Total Assets", "value": "321000000.0", "sources": []},
                        ],
                    },
                ],
            },
        },
    }

    @pytest.fixture
    def add_spgi_segments_mock_resp(self, httpx_mock: HTTPXMock) -> None:
        """Add mock response for SPGI segments."""
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/segments/",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): self.segments_response},
                "errors": {},
            },
            is_optional=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_segments_from_company_ids(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_segments_mock_resp: None,
    ) -> None:
        """
        WHEN we request SPGI's segments (using SPGI's company id)
        THEN we get back SPGI's segments
        """

        resp = await fetch_segments_from_company_ids(
            company_ids=[SPGI_ID_TRIPLE.company_id],
            segment_type=SegmentType.business,
            httpx_client=httpx_client,
        )

        expected_resp_data = {
            "results": {str(SPGI_ID_TRIPLE.company_id): self.segments_response},
            "errors": {},
        }
        # Import here to avoid circular imports
        from kfinance.domains.segments.segment_models import SegmentsBatchResp

        expected_resp = SegmentsBatchResp.model_validate(expected_resp_data)

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_segments_from_identifiers(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_segments_mock_resp: None,
    ) -> None:
        """
        WHEN we request segments for SPGI and a non-existent company
        THEN we get back segments for SPGI and an error for the non-existent company
        """

        expected_resp = GetSegmentsFromIdentifiersResp(
            results={"SPGI": SegmentsResp.model_validate(self.segments_response)},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )

        resp = await get_segments_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            segment_type=SegmentType.business,
            httpx_client=httpx_client,
        )

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_most_recent_request(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN we request most recent segments for multiple companies
        THEN we only get back the most recent segment for each company
        """

        company_ids = [1, 2]

        # Mock the segments response for both companies
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/segments/",
            json={
                "results": {"1": self.segments_response, "2": self.segments_response},
                "errors": {},
            },
        )

        expected_single_company_response = SegmentsResp.model_validate(
            {
                "currency": "USD",
                "periods": {
                    "CY2021": {
                        "period_end_date": "2021-12-31",
                        "num_months": 12,
                        "segments": self.segments_response["periods"]["CY2021"]["segments"],
                    }
                },
            }
        )

        expected_response = GetSegmentsFromIdentifiersResp(
            results={
                "C_1": expected_single_company_response,
                "C_2": expected_single_company_response,
            },
        )

        resp = await get_segments_from_identifiers(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            segment_type=SegmentType.business,
            httpx_client=httpx_client,
        )

        assert resp == expected_response

    @pytest.mark.asyncio
    async def test_empty_most_recent_request(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN we request most recent segments for multiple companies
        THEN we only get back the most recent segment for each company
        UNLESS no segments exist
        """

        company_ids = [1, 2]

        # Mock the segments response with different data for different companies
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/segments/",
            json={
                "results": {"1": {"currency": "USD", "periods": {}}, "2": self.segments_response},
                "errors": {},
            },
        )

        c_1_segments_resp = SegmentsResp.model_validate({"currency": "USD", "periods": {}})
        c_2_segments_resp = SegmentsResp.model_validate(self.segments_response)
        # Since there are multiple companies but C_2 has data, truncation should apply
        c_2_segments_resp.remove_all_periods_other_than_the_most_recent_one()

        expected_response = GetSegmentsFromIdentifiersResp(
            results={"C_1": c_1_segments_resp, "C_2": c_2_segments_resp},
        )

        resp = await get_segments_from_identifiers(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            segment_type=SegmentType.business,
            httpx_client=httpx_client,
        )

        assert resp == expected_response
