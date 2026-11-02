import httpx2
import pytest

from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.line_items.line_item_models import AlternativeLineItemMetadata
from kfinance.domains.line_items.response_notes import (
    SOURCE_LINK_NOTE,
)
from kfinance.domains.surprise.surprise_models import VisibleAlphaSurprises
from kfinance.domains.surprise.surprise_tools_va import (
    fetch_visible_alpha_surprises_from_company_ids,
    get_visible_alpha_surprises_from_identifiers,
)


SURPRISES_RESP = {
    "estimate_type": "revenue",
    "period_type": "quarterly",
    "periods": {
        "FY2026Q1": {
            "period_end_date": "2026-03-31",
            "surprises": [
                {
                    "name": "Total revenue",
                    "estimate_value": "4073777490.701441",
                    "actual_value": "4171000000.000000",
                    "pct_changed": "2.386544",
                    "sources": [
                        {
                            "type": "VA insights",
                            "url": "https://insights.visiblealpha.com/mex/SPGI_US/NMV/IS?dpid=12752992",
                        }
                    ],
                }
            ],
        },
        "FY2026Q2": {
            "period_end_date": "2026-06-30",
            "surprises": [
                {
                    "name": "Total revenue",
                    "estimate_value": "3888263363.040703",
                    "actual_value": "3678000000.000000",
                    "pct_changed": "-5.407642",
                    "sources": [
                        {
                            "type": "VA insights",
                            "url": "https://insights.visiblealpha.com/mex/SPGI_US/NMV/IS?dpid=12752992",
                        }
                    ],
                }
            ],
        },
    },
}

VA_METADATA = {
    "top_ranked_alternatives": [
        {"parameter_name": "Total revenue", "currency": "USD"},
        {"parameter_name": "Total revenue, YoY", "currency": None},
        {"parameter_name": "Total revenue - Enterprise solution", "currency": "USD"},
        {"parameter_name": "Revenue per share", "currency": "USD"},
    ]
}


class TestFetchSurprisesFromCompanyIdsVa:
    @pytest.mark.asyncio
    async def test_data_source_absent_from_payload(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock
    ) -> None:
        """
        WHEN we fetch surprises via the Visible Alpha function
        THEN data_source_type is not sent in the request body
        """
        httpx2_mock.post("https://kfinance.kensho.com/api/v1/surprise/visible_alpha").respond(
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): SURPRISES_RESP},
                "errors": {},
                "metadata": {},
            }
        )

        resp = await fetch_visible_alpha_surprises_from_company_ids(
            company_ids=[SPGI_ID_TRIPLE.company_id],
            httpx_client=httpx_client,
        )

        assert str(SPGI_ID_TRIPLE.company_id) in resp.results
        assert "data_source_type" not in httpx2_mock.calls[-1].request.content.decode()

    @pytest.mark.asyncio
    async def test_estimate_search_included_in_payload(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock
    ) -> None:
        """
        WHEN estimate_search is provided
        THEN it is included in the request payload
        """
        httpx2_mock.post(
            "https://kfinance.kensho.com/api/v1/surprise/visible_alpha",
            json={
                "company_ids": [SPGI_ID_TRIPLE.company_id],
                "estimate_search": "revenue",
            },
        ).respond(
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): SURPRISES_RESP},
                "errors": {},
                "metadata": {},
            }
        )

        resp = await fetch_visible_alpha_surprises_from_company_ids(
            company_ids=[SPGI_ID_TRIPLE.company_id],
            httpx_client=httpx_client,
            estimate_search="revenue",
        )

        assert str(SPGI_ID_TRIPLE.company_id) in resp.results

    @pytest.mark.asyncio
    async def test_returns_metadata(self, httpx_client: httpx2.AsyncClient, httpx2_mock) -> None:
        """
        WHEN the API returns metadata with ranked alternatives
        THEN the metadata is parsed correctly
        """
        httpx2_mock.post("https://kfinance.kensho.com/api/v1/surprise/visible_alpha").respond(
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): SURPRISES_RESP},
                "errors": {},
                "metadata": {str(SPGI_ID_TRIPLE.company_id): VA_METADATA},
            }
        )

        resp = await fetch_visible_alpha_surprises_from_company_ids(
            company_ids=[SPGI_ID_TRIPLE.company_id],
            httpx_client=httpx_client,
        )

        assert str(SPGI_ID_TRIPLE.company_id) in resp.metadata
        meta = resp.metadata[str(SPGI_ID_TRIPLE.company_id)]
        assert len(meta.top_ranked_alternatives) == 4
        assert meta.top_ranked_alternatives[0].parameter_name == "Total revenue"


class TestGetSurprisesFromIdentifiersVa:
    @pytest.fixture
    def add_spgi_surprises_va_mock(self, httpx2_mock) -> None:
        httpx2_mock.post("https://kfinance.kensho.com/api/v1/surprise/visible_alpha").respond(
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): SURPRISES_RESP},
                "errors": {},
                "metadata": {},
            }
        )

    @pytest.mark.asyncio
    async def test_maps_result_back_to_identifier(
        self,
        httpx_client: httpx2.AsyncClient,
        add_spgi_surprises_va_mock: None,
    ) -> None:
        """
        WHEN we request Visible Alpha surprises for SPGI
        THEN the result is keyed by the original identifier
        """
        resp = await get_visible_alpha_surprises_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
        )

        assert "SPGI" in resp.identifier_results
        expected = VisibleAlphaSurprises.model_validate(SURPRISES_RESP)
        assert resp.identifier_results["SPGI"] == expected
        assert resp.data_source == "Visible Alpha"

    @pytest.mark.asyncio
    async def test_unknown_identifier_surfaces_as_error(
        self,
        httpx_client: httpx2.AsyncClient,
        add_spgi_surprises_va_mock: None,
    ) -> None:
        """
        WHEN one identifier cannot be resolved
        THEN it surfaces in errors and the valid result is still returned
        """
        resp = await get_visible_alpha_surprises_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            httpx_client=httpx_client,
        )

        assert "SPGI" in resp.identifier_results
        assert len(resp.errors) == 1
        assert "NON-EXISTENT" in resp.errors[0]

    @pytest.mark.asyncio
    async def test_api_error_mapped_back_to_identifier(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock
    ) -> None:
        """
        WHEN the API returns an error keyed by company_id
        THEN it is mapped back to the original identifier
        """
        httpx2_mock.post("https://kfinance.kensho.com/api/v1/surprise/visible_alpha").respond(
            json={
                "results": {},
                "errors": {str(SPGI_ID_TRIPLE.company_id): "Company not found in Visible Alpha."},
                "metadata": {},
            }
        )

        resp = await get_visible_alpha_surprises_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
        )

        assert resp.identifier_results == {}
        assert any("SPGI" in e for e in resp.errors)

    @pytest.mark.asyncio
    async def test_metadata_alternative_note_added(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock
    ) -> None:
        """
        WHEN the API returns metadata
        THEN a note reminding the LLM to check estimate_search alternatives is appended
        """
        httpx2_mock.post("https://kfinance.kensho.com/api/v1/surprise/visible_alpha").respond(
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): SURPRISES_RESP},
                "errors": {},
                "metadata": {str(SPGI_ID_TRIPLE.company_id): VA_METADATA},
            }
        )

        resp = await get_visible_alpha_surprises_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
        )

        assert any("estimate_search" in note for note in resp.notes)

    @pytest.mark.asyncio
    async def test_no_metadata_no_alternative_note(
        self,
        httpx_client: httpx2.AsyncClient,
        add_spgi_surprises_va_mock: None,
    ) -> None:
        """
        WHEN the API returns no metadata
        THEN no alternatives note is added
        """
        resp = await get_visible_alpha_surprises_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
        )

        assert all("estimate_search" not in note for note in resp.notes)

    @pytest.mark.asyncio
    async def test_source_link_note_always_present(
        self,
        httpx_client: httpx2.AsyncClient,
        add_spgi_surprises_va_mock: None,
    ) -> None:
        """
        WHEN we get a valid Visible Alpha surprise result
        THEN the source link note is always included so the LLM formats sources as links
        """
        resp = await get_visible_alpha_surprises_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
        )

        assert SOURCE_LINK_NOTE in resp.notes

    @pytest.mark.asyncio
    async def test_metadata_keyed_by_identifier(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock
    ) -> None:
        """
        WHEN the API returns metadata keyed by company_id
        THEN the response metadata is re-keyed to the original identifier
        """
        httpx2_mock.post("https://kfinance.kensho.com/api/v1/surprise/visible_alpha").respond(
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): SURPRISES_RESP},
                "errors": {},
                "metadata": {str(SPGI_ID_TRIPLE.company_id): VA_METADATA},
            }
        )

        resp = await get_visible_alpha_surprises_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
        )

        assert "SPGI" in resp.metadata
        assert isinstance(resp.metadata["SPGI"], AlternativeLineItemMetadata)
