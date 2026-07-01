import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.estimates.estimates_models import Estimates
from kfinance.domains.estimates.estimates_tools_va import (
    fetch_estimates_from_company_ids_va,
    get_estimates_from_identifiers_va,
)
from kfinance.domains.line_items.line_item_models import AlternativeLineItemMetadata
from kfinance.domains.line_items.response_notes import (
    FISCAL_PERIOD_WARNING,
    FISCAL_YEAR_TERMINOLOGY_WARNING,
)


ESTIMATES_RESP = {
    "estimate_type": "consensus",
    "currency": "USD",
    "period_type": "quarterly",
    "periods": {
        "FY2025Q4": {
            "period_end_date": "2025-12-31",
            "estimates": [
                {"name": "iPhone Unit Sales - # of Estimates", "value": "3.000000"},
                {"name": "iPhone Unit Sales Consensus Mean", "value": "225000000.0"},
            ],
        },
        "FY2026Q1": {
            "period_end_date": "2026-03-31",
            "estimates": [
                {"name": "iPhone Unit Sales - # of Estimates", "value": "2.000000"},
                {"name": "iPhone Unit Sales Consensus Mean", "value": "215000000.0"},
            ],
        },
    },
}

VA_METADATA = {
    "top_ranked_alternatives": [
        {"parameter_name": "Mac Unit Sales Consensus Mean", "currency": None},
        {"parameter_name": "iPad Unit Sales Consensus Mean", "currency": None},
    ]
}


class TestFetchEstimatesFromCompanyIdsVa:
    @pytest.mark.asyncio
    async def test_data_source_absent_from_payload(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN we fetch estimates via the VA function
        THEN data_source_type is not sent in the request body
        """
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/estimates/",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): ESTIMATES_RESP},
                "errors": {},
                "metadata": {},
            },
        )

        resp = await fetch_estimates_from_company_ids_va(
            company_ids=[SPGI_ID_TRIPLE.company_id],
            httpx_client=httpx_client,
        )

        assert str(SPGI_ID_TRIPLE.company_id) in resp.results
        assert "data_source_type" not in httpx_mock.get_requests()[-1].content.decode()

    @pytest.mark.asyncio
    async def test_estimate_search_included_in_payload(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN estimate_search is provided
        THEN it is included in the request payload
        """
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/estimates/",
            match_json={
                "company_ids": [SPGI_ID_TRIPLE.company_id],
                "estimate_type": "consensus",
                "estimate_search": "iPhone unit sales",
            },
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): ESTIMATES_RESP},
                "errors": {},
                "metadata": {},
            },
        )

        resp = await fetch_estimates_from_company_ids_va(
            company_ids=[SPGI_ID_TRIPLE.company_id],
            httpx_client=httpx_client,
            estimate_search="iPhone unit sales",
        )

        assert str(SPGI_ID_TRIPLE.company_id) in resp.results

    @pytest.mark.asyncio
    async def test_returns_metadata(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN the API returns metadata with ranked alternatives
        THEN the metadata is parsed correctly
        """
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/estimates/",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): ESTIMATES_RESP},
                "errors": {},
                "metadata": {str(SPGI_ID_TRIPLE.company_id): VA_METADATA},
            },
        )

        resp = await fetch_estimates_from_company_ids_va(
            company_ids=[SPGI_ID_TRIPLE.company_id],
            httpx_client=httpx_client,
        )

        assert str(SPGI_ID_TRIPLE.company_id) in resp.metadata
        meta = resp.metadata[str(SPGI_ID_TRIPLE.company_id)]
        assert len(meta.top_ranked_alternatives) == 2
        assert meta.top_ranked_alternatives[0].parameter_name == "Mac Unit Sales Consensus Mean"


class TestGetEstimatesFromIdentifiersVa:
    @pytest.fixture
    def add_spgi_estimates_va_mock(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/estimates/",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): ESTIMATES_RESP},
                "errors": {},
                "metadata": {},
            },
            is_optional=True,
        )

    @pytest.mark.asyncio
    async def test_maps_result_back_to_identifier(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_estimates_va_mock: None,
    ) -> None:
        """
        WHEN we request VA estimates for SPGI
        THEN the result is keyed by the original identifier
        """
        resp = await get_estimates_from_identifiers_va(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
        )

        assert "SPGI" in resp.identifier_results
        assert resp.identifier_results["SPGI"] == Estimates.model_validate(ESTIMATES_RESP)

    @pytest.mark.asyncio
    async def test_unknown_identifier_surfaces_as_error(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_estimates_va_mock: None,
    ) -> None:
        """
        WHEN one identifier cannot be resolved
        THEN it surfaces in errors and the valid result is still returned
        """
        resp = await get_estimates_from_identifiers_va(
            identifiers=["SPGI", "non-existent"],
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
            url="https://kfinance.kensho.com/api/v1/estimates/",
            json={
                "results": {},
                "errors": {str(SPGI_ID_TRIPLE.company_id): "Company not found in Visible Alpha."},
                "metadata": {},
            },
        )

        resp = await get_estimates_from_identifiers_va(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
        )

        assert resp.identifier_results == {}
        assert any("SPGI" in e for e in resp.errors)

    @pytest.mark.asyncio
    async def test_metadata_alternative_note_added(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN the API returns metadata
        THEN a note reminding the LLM to check estimate_search alternatives is appended
        """
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/estimates/",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): ESTIMATES_RESP},
                "errors": {},
                "metadata": {str(SPGI_ID_TRIPLE.company_id): VA_METADATA},
            },
        )

        resp = await get_estimates_from_identifiers_va(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
        )

        assert any("estimate_search" in note for note in resp.notes)

    @pytest.mark.asyncio
    async def test_no_metadata_no_alternative_note(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_estimates_va_mock: None,
    ) -> None:
        """
        WHEN the API returns no metadata
        THEN no alternatives note is added
        """
        resp = await get_estimates_from_identifiers_va(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
        )

        assert all("estimate_search" not in note for note in resp.notes)

    @pytest.mark.asyncio
    async def test_fiscal_period_notes_always_present(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_estimates_va_mock: None,
    ) -> None:
        """
        WHEN we get a valid VA estimates result
        THEN fiscal period notes are included (estimates are always fiscal)
        """
        resp = await get_estimates_from_identifiers_va(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
        )

        assert FISCAL_PERIOD_WARNING in resp.notes
        assert FISCAL_YEAR_TERMINOLOGY_WARNING in resp.notes

    @pytest.mark.asyncio
    async def test_metadata_keyed_by_identifier(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN the API returns metadata keyed by company_id
        THEN the response metadata is re-keyed to the original identifier
        """
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/estimates/",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): ESTIMATES_RESP},
                "errors": {},
                "metadata": {str(SPGI_ID_TRIPLE.company_id): VA_METADATA},
            },
        )

        resp = await get_estimates_from_identifiers_va(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
        )

        assert "SPGI" in resp.metadata
        assert isinstance(resp.metadata["SPGI"], AlternativeLineItemMetadata)
