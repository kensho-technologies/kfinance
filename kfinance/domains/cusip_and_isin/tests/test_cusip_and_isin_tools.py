from typing import Literal

import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.cusip_and_isin.cusip_and_isin_tools import (
    GetCusipOrIsinFromIdentifiersResp,
    fetch_cusip_or_isin_from_security_id,
    get_cusip_or_isin_from_identifiers,
)


SPGI_CUSIP = "78409V104"
SPGI_ISIN = "US78409V104"


class TestCusipAndIsin:
    @pytest.fixture
    def add_spgi_cusip_and_isin_mock_resp(self, httpx_mock: HTTPXMock) -> None:
        """Add mock responses for both CUSIP and ISIN endpoints."""
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/isin/{SPGI_ID_TRIPLE.security_id}",
            json={"isin": SPGI_ISIN},
            is_optional=True,
        )
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/cusip/{SPGI_ID_TRIPLE.security_id}",
            json={"cusip": SPGI_CUSIP},
            is_optional=True,
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "cusip_or_isin, expected_response", [("cusip", SPGI_CUSIP), ("isin", SPGI_ISIN)]
    )
    async def test_fetch_cusip_and_isin_from_security_id(
        self,
        cusip_or_isin: Literal["cusip", "isin"],
        expected_response: str,
        httpx_client: httpx.AsyncClient,
        add_spgi_cusip_and_isin_mock_resp: None,
    ) -> None:
        """
        WHEN we request SPGI's cusip or isin (using SPGI's security id)
        THEN we get back SPGI's cusip or isin
        """

        resp = await fetch_cusip_or_isin_from_security_id(
            security_id=SPGI_ID_TRIPLE.security_id,
            cusip_or_isin=cusip_or_isin,
            httpx_client=httpx_client,
        )
        assert resp == expected_response

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "cusip_or_isin, expected_response", [("cusip", SPGI_CUSIP), ("isin", SPGI_ISIN)]
    )
    async def test_get_cusip_or_isin_from_identifiers(
        self,
        cusip_or_isin: Literal["cusip", "isin"],
        expected_response: str,
        httpx_client: httpx.AsyncClient,
        add_spgi_cusip_and_isin_mock_resp: None,
    ) -> None:
        """
        WHEN we request cusip or isin for SPGI and a private company
        THEN we get back cusip or isin for SPGI and an error for the private company.
        """

        expected_resp = GetCusipOrIsinFromIdentifiersResp(
            identifier_results={"SPGI": expected_response},
            errors=["private_company is a private company without a security_id."],
        )

        resp = await get_cusip_or_isin_from_identifiers(
            identifiers=["SPGI", "private_company"],
            cusip_or_isin=cusip_or_isin,
            httpx_client=httpx_client,
        )

        assert resp == expected_resp
