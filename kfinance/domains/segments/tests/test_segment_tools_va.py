import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX
from kfinance.domains.line_items.response_notes import (
    FISCAL_PERIOD_WARNING,
    FISCAL_YEAR_TERMINOLOGY_WARNING,
)
from kfinance.domains.segments.segment_models import SegmentsResp, SegmentType
from kfinance.domains.segments.segment_tools_va import (
    fetch_segments_from_company_ids_va,
    get_segments_from_identifiers_va,
)


SEGMENTS_RESP = {
    "currency": "USD",
    "periods": {
        "CY2023": {
            "period_end_date": "2023-12-31",
            "num_months": 12,
            "segments": [
                {
                    "name": "iPhone",
                    "line_items": [
                        {"name": "Revenue", "value": "200583000000.0", "sources": []},
                    ],
                },
                {
                    "name": "Services",
                    "line_items": [
                        {"name": "Revenue", "value": "85200000000.0", "sources": []},
                    ],
                },
            ],
        },
        "CY2022": {
            "period_end_date": "2022-12-31",
            "num_months": 12,
            "segments": [
                {
                    "name": "iPhone",
                    "line_items": [
                        {"name": "Revenue", "value": "205489000000.0", "sources": []},
                    ],
                },
            ],
        },
    },
}


class TestFetchSegmentsFromCompanyIdsVa:
    @pytest.mark.asyncio
    async def test_data_source_absent_from_payload(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN we fetch segments via the VA function
        THEN data_source_type is not sent in the request body
        """
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/segments/",
            json={"results": {str(SPGI_ID_TRIPLE.company_id): SEGMENTS_RESP}, "errors": {}},
        )

        resp = await fetch_segments_from_company_ids_va(
            company_ids=[SPGI_ID_TRIPLE.company_id],
            segment_type=SegmentType.business,
            httpx_client=httpx_client,
        )

        assert str(SPGI_ID_TRIPLE.company_id) in resp.results
        assert "data_source_type" not in httpx_mock.get_requests()[-1].content.decode()


class TestGetSegmentsFromIdentifiersVa:
    @pytest.fixture
    def add_spgi_segments_va_mock(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/segments/",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): SEGMENTS_RESP},
                "errors": {},
            },
            is_optional=True,
        )

    @pytest.mark.asyncio
    async def test_maps_result_back_to_identifier(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_segments_va_mock: None,
    ) -> None:
        """
        WHEN we request VA segments for SPGI
        THEN the result is keyed by the original identifier
        """
        resp = await get_segments_from_identifiers_va(
            identifiers=["SPGI"],
            segment_type=SegmentType.business,
            httpx_client=httpx_client,
        )

        assert "SPGI" in resp.identifier_results
        expected = SegmentsResp.model_validate(SEGMENTS_RESP)
        expected.data_source = "Visible Alpha"
        assert resp.identifier_results["SPGI"] == expected

    @pytest.mark.asyncio
    async def test_unknown_identifier_surfaces_as_error(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_segments_va_mock: None,
    ) -> None:
        """
        WHEN one identifier cannot be resolved
        THEN it surfaces in errors and the valid result is still returned
        """
        resp = await get_segments_from_identifiers_va(
            identifiers=["SPGI", "non-existent"],
            segment_type=SegmentType.business,
            httpx_client=httpx_client,
        )

        assert "SPGI" in resp.identifier_results
        assert len(resp.errors) == 1
        assert "NON-EXISTENT" in resp.errors[0]

    @pytest.mark.asyncio
    async def test_api_error_mapped_back_to_identifier(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN the API returns an error keyed by company_id
        THEN it is mapped back to the original identifier
        """
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/segments/",
            json={
                "results": {},
                "errors": {str(SPGI_ID_TRIPLE.company_id): "Company not found in Visible Alpha."},
            },
        )

        resp = await get_segments_from_identifiers_va(
            identifiers=["SPGI"],
            segment_type=SegmentType.business,
            httpx_client=httpx_client,
        )

        assert resp.identifier_results == {}
        assert any("SPGI" in e for e in resp.errors)

    @pytest.mark.asyncio
    async def test_fiscal_note_added_for_fiscal_calendar_type(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN calendar_type is fiscal
        THEN fiscal period notes are included in the response
        """
        from kfinance.domains.line_items.line_item_models import CalendarType

        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/segments/",
            json={"results": {str(SPGI_ID_TRIPLE.company_id): SEGMENTS_RESP}, "errors": {}},
        )

        resp = await get_segments_from_identifiers_va(
            identifiers=["SPGI"],
            segment_type=SegmentType.business,
            httpx_client=httpx_client,
            calendar_type=CalendarType.fiscal,
        )

        assert FISCAL_PERIOD_WARNING in resp.notes
        assert FISCAL_YEAR_TERMINOLOGY_WARNING in resp.notes

    @pytest.mark.asyncio
    async def test_most_recent_trimmed_for_multi_company(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN requesting multiple companies with no date filters
        THEN only the most recent period is kept per company
        """
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/segments/",
            json={
                "results": {"1": SEGMENTS_RESP, "2": SEGMENTS_RESP},
                "errors": {},
            },
        )

        resp = await get_segments_from_identifiers_va(
            identifiers=[f"{COMPANY_ID_PREFIX}1", f"{COMPANY_ID_PREFIX}2"],
            segment_type=SegmentType.business,
            httpx_client=httpx_client,
        )

        for result in resp.identifier_results.values():
            assert len(result.periods) == 1
