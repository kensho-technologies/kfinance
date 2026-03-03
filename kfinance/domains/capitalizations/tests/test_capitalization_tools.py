from copy import deepcopy
from datetime import date
from decimal import Decimal

import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.client.models.decimal_with_unit import Money, Shares
from kfinance.conftest import SPGI_COMPANY_ID, SPGI_ID_TRIPLE
from kfinance.domains.capitalizations.capitalization_models import (
    Capitalization,
    Capitalizations,
    DailyCapitalization,
)
from kfinance.domains.capitalizations.capitalization_tools import (
    GetCapitalizationFromIdentifiersResp,
    fetch_capitalizations_from_company_id,
    get_capitalizations_from_identifiers,
)


CAPITALIZATION_RESP = {
    "currency": "USD",
    "market_caps": [
        {
            "date": "2024-04-10",
            "market_cap": "132766738270.000000",
            "tev": "147455738270.000000",
            "shares_outstanding": 313099562,
        },
        {
            "date": "2024-04-11",
            "market_cap": "132416066761.000000",
            "tev": "147105066761.000000",
            "shares_outstanding": 313099562,
        },
    ],
}


@pytest.fixture
def add_spgi_capitalizations_mock_resp(httpx_mock: HTTPXMock) -> None:
    """Add mock response for SPGI capitalization data."""
    httpx_mock.add_response(
        method="GET",
        url=f"https://kfinance.kensho.com/api/v1/market_cap/{SPGI_COMPANY_ID}/none/none",
        json=CAPITALIZATION_RESP,
    )


class TestCapitalizations:
    expected_capitalizations_response = Capitalizations(
        market_caps=[
            DailyCapitalization(
                date=date(2024, 4, 10),
                market_cap=Money(value=Decimal(132766738270), unit="USD"),
                tev=Money(value=Decimal(147455738270), unit="USD"),
                shares_outstanding=Shares(value=Decimal("313099562")),
            ),
            DailyCapitalization(
                date=date(2024, 4, 11),
                market_cap=Money(value=Decimal(132416066761), unit="USD"),
                tev=Money(value=Decimal(147105066761), unit="USD"),
                shares_outstanding=Shares(value=Decimal("313099562")),
            ),
        ]
    )

    @pytest.mark.asyncio
    async def test_fetch_capitalizations_from_company_id(
        self, httpx_client: httpx.AsyncClient, add_spgi_capitalizations_mock_resp: None
    ) -> None:
        """
        WHEN we request SPGI's capitalizations (using SPGI's company id)
        THEN we get back SPGI's capitalizations.
        """

        resp = await fetch_capitalizations_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            start_date=None,
            end_date=None,
            httpx_client=httpx_client,
        )
        assert resp == self.expected_capitalizations_response

    @pytest.mark.asyncio
    async def test_get_capitalizations_from_identifiers(
        self, httpx_client: httpx.AsyncClient, add_spgi_capitalizations_mock_resp: None
    ) -> None:
        """
        WHEN we fetch market caps for SPGI and a non-existent company
        THEN we get back SPGI's market caps and an error for the non-existent company.
        """
        expected_spgi_resp = deepcopy(self.expected_capitalizations_response)
        for capitalization in expected_spgi_resp.capitalizations:
            capitalization.tev = None
            capitalization.shares_outstanding = None
        expected_resp = GetCapitalizationFromIdentifiersResp(
            capitalization=Capitalization.market_cap,
            results={"SPGI": expected_spgi_resp},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )
        resp = await get_capitalizations_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            capitalization=Capitalization.market_cap,
            start_date=None,
            end_date=None,
            httpx_client=httpx_client,
        )
        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_capitalizations_from_identifiers_truncation(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN we fetch market caps for more than one company without start or end dates
        THEN we get back only the most recent market caps
        """

        for company_id in [1, 2]:
            httpx_mock.add_response(
                method="GET",
                url=f"https://kfinance.kensho.com/api/v1/market_cap/{company_id}/none/none",
                json=CAPITALIZATION_RESP,
            )

        expected_company_resp = deepcopy(self.expected_capitalizations_response)
        # truncate expected response to only include the last available day.
        expected_company_resp.capitalizations = expected_company_resp.capitalizations[-1:]
        expected_company_resp.capitalizations[-1].tev = None
        expected_company_resp.capitalizations[-1].shares_outstanding = None
        # ensure that we retain the data for the last available date (2024-04-11).
        assert expected_company_resp.capitalizations[-1].date == date(2024, 4, 11)

        expected_resp = GetCapitalizationFromIdentifiersResp(
            capitalization=Capitalization.market_cap,
            results={"C_1": expected_company_resp, "C_2": expected_company_resp},
        )
        resp = await get_capitalizations_from_identifiers(
            identifiers=["C_1", "C_2"],
            capitalization=Capitalization.market_cap,
            start_date=None,
            end_date=None,
            httpx_client=httpx_client,
        )
        assert resp == expected_resp