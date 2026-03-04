import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.client.models.date_and_period_models import Periodicity
from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX
from kfinance.domains.prices.price_models import HistoryMetadataResp, PriceHistory
from kfinance.domains.prices.price_tools import (
    GetHistoryMetadataFromIdentifiersResp,
    GetPricesFromIdentifiersResp,
    fetch_history_metadata_from_trading_item_id,
    fetch_price_history_from_trading_item_id,
    get_history_metadata_from_identifiers,
    get_prices_from_identifiers,
)


class TestPrices:
    prices_resp = {
        "currency": "USD",
        "prices": [
            {
                "date": "2024-04-11",
                "open": "424.260000",
                "high": "425.990000",
                "low": "422.040000",
                "close": "422.920000",
                "volume": "1129158",
            },
            {
                "date": "2024-04-12",
                "open": "419.230000",
                "high": "421.940000",
                "low": "416.450000",
                "close": "417.810000",
                "volume": "1182229",
            },
        ],
    }

    @pytest.fixture
    def add_spgi_prices_mock_resp(self, httpx_mock: HTTPXMock) -> None:
        """Add mock response for SPGI prices."""
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/pricing/{SPGI_ID_TRIPLE.trading_item_id}/none/none/day/adjusted",
            json=self.prices_resp,
            is_optional=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_price_history_from_trading_item_id(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_prices_mock_resp: None,
    ) -> None:
        """
        WHEN we request SPGI's price history (using SPGI's trading item id)
        THEN we get back SPGI's price history
        """

        resp = await fetch_price_history_from_trading_item_id(
            trading_item_id=SPGI_ID_TRIPLE.trading_item_id,
            httpx_client=httpx_client,
        )

        expected_resp = PriceHistory.model_validate(self.prices_resp)
        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_prices_from_identifiers(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_prices_mock_resp: None,
    ) -> None:
        """
        WHEN we request prices for SPGI and a non-existent company
        THEN we get back prices for SPGI and an error for the non-existent company
        """

        expected_resp = GetPricesFromIdentifiersResp(
            results={"SPGI": PriceHistory.model_validate(self.prices_resp)},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )

        resp = await get_prices_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            httpx_client=httpx_client,
        )

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_most_recent_request(self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock) -> None:
        """
        WHEN we request most recent prices for multiple companies
        THEN we only get back the most recent prices for each company
        """

        company_ids = [1, 2]

        # Mock the price response for both companies
        for trading_item_id in company_ids:
            httpx_mock.add_response(
                method="GET",
                url=f"https://kfinance.kensho.com/api/v1/pricing/{trading_item_id}/none/none/day/adjusted",
                json=self.prices_resp,
            )

        expected_single_company_response = PriceHistory.model_validate({
            "prices": [
                {
                    "date": "2024-04-12",
                    "open": {"value": "419.23", "unit": "USD"},
                    "high": {"value": "421.94", "unit": "USD"},
                    "low": {"value": "416.45", "unit": "USD"},
                    "close": {"value": "417.81", "unit": "USD"},
                    "volume": {"value": "1182229", "unit": "Shares"},
                }
            ]
        })

        expected_response = GetPricesFromIdentifiersResp(
            results={
                "C_1": expected_single_company_response,
                "C_2": expected_single_company_response,
            },
        )

        resp = await get_prices_from_identifiers(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            httpx_client=httpx_client,
        )

        assert resp == expected_response

    @pytest.mark.asyncio
    async def test_get_prices_with_date_range(
        self,
        httpx_client: httpx.AsyncClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """
        WHEN we request prices with a specific date range and periodicity
        THEN we get back prices with the correct parameters
        """
        from datetime import date

        start_date = date(2024, 4, 1)
        end_date = date(2024, 4, 30)
        periodicity = Periodicity.week

        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/pricing/{SPGI_ID_TRIPLE.trading_item_id}/2024-04-01/2024-04-30/week/unadjusted",
            json=self.prices_resp,
        )

        resp = await fetch_price_history_from_trading_item_id(
            trading_item_id=SPGI_ID_TRIPLE.trading_item_id,
            httpx_client=httpx_client,
            start_date=start_date,
            end_date=end_date,
            periodicity=periodicity,
            adjusted=False,
        )

        expected_resp = PriceHistory.model_validate(self.prices_resp)
        assert resp == expected_resp


class TestHistoryMetadata:
    metadata_resp = {
        "currency": "USD",
        "exchange_name": "NYSE",
        "first_trade_date": "1968-01-02",
        "instrument_type": "Equity",
        "symbol": "SPGI",
    }

    @pytest.fixture
    def add_spgi_metadata_mock_resp(self, httpx_mock: HTTPXMock) -> None:
        """Add mock response for SPGI history metadata."""
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/pricing/{SPGI_ID_TRIPLE.trading_item_id}/metadata",
            json=self.metadata_resp,
            is_optional=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_history_metadata_from_trading_item_id(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_metadata_mock_resp: None,
    ) -> None:
        """
        WHEN we request SPGI's history metadata (using SPGI's trading item id)
        THEN we get back SPGI's history metadata
        """

        resp = await fetch_history_metadata_from_trading_item_id(
            trading_item_id=SPGI_ID_TRIPLE.trading_item_id,
            httpx_client=httpx_client,
        )

        expected_resp = HistoryMetadataResp.model_validate(self.metadata_resp)
        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_history_metadata_from_identifiers(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_metadata_mock_resp: None,
    ) -> None:
        """
        WHEN we request the history metadata for SPGI and a non-existent company
        THEN we get back SPGI's history metadata and an error for the non-existent company
        """

        expected_resp = GetHistoryMetadataFromIdentifiersResp(
            results={"SPGI": HistoryMetadataResp.model_validate(self.metadata_resp)},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )

        resp = await get_history_metadata_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            httpx_client=httpx_client,
        )

        assert resp == expected_resp