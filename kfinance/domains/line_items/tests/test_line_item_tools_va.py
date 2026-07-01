import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX
from kfinance.domains.line_items.line_item_models import (
    AlternativeLineItemMetadata,
    LineItemResp,
)
from kfinance.domains.line_items.line_item_tools_va import (
    fetch_line_item_from_company_ids_va,
    get_financial_line_item_from_identifiers_va,
)
from kfinance.domains.line_items.response_notes import (
    SOURCE_LINK_NOTE,
)


LINE_ITEM_RESP = {
    "currency": "USD",
    "periods": {
        "CY2022": {
            "period_end_date": "2022-12-31",
            "num_months": 12,
            "line_item": {"name": "iPhone Revenue", "value": "205489000000.0", "sources": []},
        },
        "CY2023": {
            "period_end_date": "2023-12-31",
            "num_months": 12,
            "line_item": {"name": "iPhone Revenue", "value": "200583000000.0", "sources": []},
        },
    },
}

VA_METADATA = {
    "top_ranked_alternatives": [
        {"parameter_name": "Mac Revenue", "currency": "USD"},
        {"parameter_name": "Services Revenue", "currency": "USD"},
    ]
}


class TestFetchLineItemFromCompanyIdsVa:
    @pytest.mark.asyncio
    async def test_data_source_absent_from_payload(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN we fetch a line item via the VA function
        THEN data_source_type is not sent in the request body
        """
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/line_item/",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): LINE_ITEM_RESP},
                "errors": {},
                "metadata": {},
            },
        )

        resp = await fetch_line_item_from_company_ids_va(
            company_ids=[SPGI_ID_TRIPLE.company_id],
            line_item="iPhone revenue",
            httpx_client=httpx_client,
        )

        assert str(SPGI_ID_TRIPLE.company_id) in resp.results
        assert "data_source_type" not in httpx_mock.get_requests()[-1].content.decode()

    @pytest.mark.asyncio
    async def test_returns_metadata(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN the API returns metadata with alternatives
        THEN the metadata is parsed into AlternativeLineItemMetadata
        """
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/line_item/",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): LINE_ITEM_RESP},
                "errors": {},
                "metadata": {str(SPGI_ID_TRIPLE.company_id): VA_METADATA},
            },
        )

        resp = await fetch_line_item_from_company_ids_va(
            company_ids=[SPGI_ID_TRIPLE.company_id],
            line_item="iPhone revenue",
            httpx_client=httpx_client,
        )

        assert str(SPGI_ID_TRIPLE.company_id) in resp.metadata
        meta = resp.metadata[str(SPGI_ID_TRIPLE.company_id)]
        assert len(meta.top_ranked_alternatives) == 2
        assert meta.top_ranked_alternatives[0].parameter_name == "Mac Revenue"


class TestGetFinancialLineItemFromIdentifiersVa:
    @pytest.fixture
    def add_spgi_line_item_va_mock(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/line_item/",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): LINE_ITEM_RESP},
                "errors": {},
                "metadata": {},
            },
            is_optional=True,
        )

    @pytest.mark.asyncio
    async def test_maps_result_back_to_identifier(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_line_item_va_mock: None,
    ) -> None:
        """
        WHEN we request a VA line item for SPGI
        THEN the result is keyed by the original identifier, not the company_id
        """
        resp = await get_financial_line_item_from_identifiers_va(
            identifiers=["SPGI"],
            line_item="iPhone revenue",
            httpx_client=httpx_client,
        )

        assert "SPGI" in resp.identifier_results
        assert resp.identifier_results["SPGI"] == LineItemResp.model_validate(LINE_ITEM_RESP)

    @pytest.mark.asyncio
    async def test_unknown_identifier_surfaces_as_error(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_line_item_va_mock: None,
    ) -> None:
        """
        WHEN one identifier cannot be resolved
        THEN it surfaces in errors and the valid result is still returned
        """
        resp = await get_financial_line_item_from_identifiers_va(
            identifiers=["SPGI", "non-existent"],
            line_item="iPhone revenue",
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
        THEN it is mapped back to the original identifier in the response
        """
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/line_item/",
            json={
                "results": {},
                "errors": {str(SPGI_ID_TRIPLE.company_id): "Company not found in Visible Alpha."},
                "metadata": {},
            },
        )

        resp = await get_financial_line_item_from_identifiers_va(
            identifiers=["SPGI"],
            line_item="iPhone revenue",
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
        THEN a note reminding the LLM to check alternatives is appended
        """
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/line_item/",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): LINE_ITEM_RESP},
                "errors": {},
                "metadata": {str(SPGI_ID_TRIPLE.company_id): VA_METADATA},
            },
        )

        resp = await get_financial_line_item_from_identifiers_va(
            identifiers=["SPGI"],
            line_item="iPhone revenue",
            httpx_client=httpx_client,
        )

        assert any("top_ranked_alternatives" in note for note in resp.notes)

    @pytest.mark.asyncio
    async def test_no_metadata_no_alternative_note(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_line_item_va_mock: None,
    ) -> None:
        """
        WHEN the API returns no metadata
        THEN no alternatives note is added
        """
        resp = await get_financial_line_item_from_identifiers_va(
            identifiers=["SPGI"],
            line_item="iPhone revenue",
            httpx_client=httpx_client,
        )

        assert all("top_ranked_alternatives" not in note for note in resp.notes)

    @pytest.mark.asyncio
    async def test_source_link_note_always_present(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_line_item_va_mock: None,
    ) -> None:
        """
        WHEN we get a valid VA line item result
        THEN the source link note is always included
        """
        resp = await get_financial_line_item_from_identifiers_va(
            identifiers=["SPGI"],
            line_item="iPhone revenue",
            httpx_client=httpx_client,
        )

        assert SOURCE_LINK_NOTE in resp.notes

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
            url="https://kfinance.kensho.com/api/v1/line_item/",
            json={
                "results": {"1": LINE_ITEM_RESP, "2": LINE_ITEM_RESP},
                "errors": {},
                "metadata": {},
            },
        )

        resp = await get_financial_line_item_from_identifiers_va(
            identifiers=[f"{COMPANY_ID_PREFIX}1", f"{COMPANY_ID_PREFIX}2"],
            line_item="iPhone revenue",
            httpx_client=httpx_client,
        )

        for result in resp.identifier_results.values():
            assert len(result.periods) == 1

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
            url="https://kfinance.kensho.com/api/v1/line_item/",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): LINE_ITEM_RESP},
                "errors": {},
                "metadata": {str(SPGI_ID_TRIPLE.company_id): VA_METADATA},
            },
        )

        resp = await get_financial_line_item_from_identifiers_va(
            identifiers=["SPGI"],
            line_item="iPhone revenue",
            httpx_client=httpx_client,
        )

        assert "SPGI" in resp.metadata
        assert isinstance(resp.metadata["SPGI"], AlternativeLineItemMetadata)
