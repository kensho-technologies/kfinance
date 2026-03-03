import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.conftest import SPGI_COMPANY_ID, SPGI_ID_TRIPLE
from kfinance.domains.business_relationships.business_relationship_models import (
    BusinessRelationshipType,
    RelationshipResponse,
)
from kfinance.domains.business_relationships.business_relationship_tools import (
    GetBusinessRelationshipFromIdentifiersResp,
    fetch_business_relationship_from_company_id,
    get_business_relationship_from_identifiers,
)
from kfinance.domains.companies.company_models import CompanyIdAndName


@pytest.fixture
def add_spgi_supplier_mock_resp(httpx_mock: HTTPXMock) -> None:
    """Add mock response for SPGI supplier relationship."""
    httpx_mock.add_response(
        method="GET",
        url=f"https://kfinance.kensho.com/api/v1/relationship/{SPGI_COMPANY_ID}/supplier",
        json={
            "current": [{"company_id": 883103, "company_name": "CRISIL Limited"}],
            "previous": [
                {"company_id": 472898, "company_name": "Morgan Stanley"},
                {"company_id": 8182358, "company_name": "Eloqua, Inc."},
            ],
        },
    )


class TestBusinessRelationships:
    expected_spgi_relationship_response = RelationshipResponse(
        current=[CompanyIdAndName(company_id=883103, company_name="CRISIL Limited")],
        previous=[
            CompanyIdAndName(company_id=472898, company_name="Morgan Stanley"),
            CompanyIdAndName(company_id=8182358, company_name="Eloqua, Inc."),
        ],
    )

    @pytest.mark.asyncio
    async def test_fetch_business_relationship_from_company_id(
        self, httpx_client: httpx.AsyncClient, add_spgi_supplier_mock_resp: None
    ) -> None:
        """
        WHEN we fetch SPGI's supplier using SPGI's company id
        THEN we get back a RelationshipResponse with SPGI's suppliers.
        """

        resp = await fetch_business_relationship_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            business_relationship=BusinessRelationshipType.supplier,
            httpx_client=httpx_client,
        )

        assert resp == self.expected_spgi_relationship_response

    @pytest.mark.asyncio
    async def test_get_business_relationship_from_identifiers(
        self, httpx_client: httpx.AsyncClient, add_spgi_supplier_mock_resp: None
    ) -> None:
        """
        WHEN we fetch suppliers for SPGI and a non-existent company
        THEN we get back SPGI's suppliers and an error for the non-existent company.
        """

        expected_resp = GetBusinessRelationshipFromIdentifiersResp(
            business_relationship=BusinessRelationshipType.supplier,
            results={"SPGI": self.expected_spgi_relationship_response},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )
        resp = await get_business_relationship_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            business_relationship=BusinessRelationshipType.supplier,
            httpx_client=httpx_client,
        )

        assert resp == expected_resp
