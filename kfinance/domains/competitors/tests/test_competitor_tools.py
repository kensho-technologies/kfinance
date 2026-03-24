import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.conftest import SPGI_COMPANY_ID, SPGI_ID_TRIPLE
from kfinance.domains.companies.company_models import CompanyIdAndName
from kfinance.domains.competitors.competitor_models import (
    CompetitorResponse,
    CompetitorSource,
)
from kfinance.domains.competitors.competitor_tools import (
    GetCompetitorsFromIdentifiersResp,
    fetch_competitors_from_company_id,
    get_competitors_from_identifiers,
)


@pytest.fixture
def add_spgi_competitors_mock_resp(httpx_mock: HTTPXMock) -> None:
    """Add mock response for SPGI competitors."""
    httpx_mock.add_response(
        method="GET",
        url=f"https://kfinance.kensho.com/api/v1/competitors/{SPGI_COMPANY_ID}",
        json={
            "competitors": [
                {"company_id": 35352, "company_name": "The Descartes Systems Group Inc."},
                {"company_id": 4003514, "company_name": "London Stock Exchange Group plc"},
            ]
        },
    )


class TestCompetitors:
    expected_spgi_competitors_response = CompetitorResponse(
        competitors=[
            CompanyIdAndName(company_id=35352, company_name="The Descartes Systems Group Inc."),
            CompanyIdAndName(company_id=4003514, company_name="London Stock Exchange Group plc"),
        ]
    )

    @pytest.mark.asyncio
    async def test_fetch_competitors_from_company_id(
        self, httpx_client: httpx.AsyncClient, add_spgi_competitors_mock_resp: None
    ) -> None:
        """
        WHEN we request SPGI's competitors (using SPGI's company id)
        THEN we get back SPGI's competitors.
        """

        resp = await fetch_competitors_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            competitor_source=CompetitorSource.all,
            httpx_client=httpx_client,
        )
        assert resp == self.expected_spgi_competitors_response

    @pytest.mark.asyncio
    async def test_get_competitors_from_identifiers(
        self, httpx_client: httpx.AsyncClient, add_spgi_competitors_mock_resp: None
    ) -> None:
        """
        WHEN we fetch competitors for SPGI and a non-existent company
        THEN we get back SPGI's competitors and an error for the non-existent company.
        """

        expected_resp = GetCompetitorsFromIdentifiersResp(
            results={"SPGI": self.expected_spgi_competitors_response},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )

        resp = await get_competitors_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            competitor_source=CompetitorSource.all,
            httpx_client=httpx_client,
        )

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_fetch_competitors_http_404(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN the server returns a 404 for a competitors request
        THEN the error is caught by the batch executor and returned as a user-friendly error
        """

        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/competitors/{SPGI_COMPANY_ID}",
            status_code=404,
        )

        expected_resp = GetCompetitorsFromIdentifiersResp(
            results={},
            errors=["No result found for SPGI."],
        )

        resp = await get_competitors_from_identifiers(
            identifiers=["SPGI"],
            competitor_source=CompetitorSource.all,
            httpx_client=httpx_client,
        )

        assert resp == expected_resp
