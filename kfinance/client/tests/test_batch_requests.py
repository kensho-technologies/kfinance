from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import time
from typing import Any, Dict
from unittest import TestCase
from unittest.mock import PropertyMock, patch

import pytest
import requests
import requests_mock

from kfinance.client.batch_request_handling import MAX_WORKERS_CAP
from kfinance.client.fetch import KFinanceApiClient
from kfinance.client.kfinance import Companies, Company, Ticker, TradingItem, TradingItems
from kfinance.client.models.decimal_with_unit import Money, Shares
from kfinance.domains.prices.price_models import PriceHistory, Prices


@pytest.fixture(autouse=True)
def mock_method():
    with patch(
        "kfinance.client.fetch.KFinanceApiClient.access_token", return_value="fake_access_token"
    ):
        yield


class TestTradingItem(TestCase):
    def setUp(self):
        self.kfinance_api_client = KFinanceApiClient(refresh_token="fake_refresh_token")
        self.kfinance_api_client_with_thread_pool = KFinanceApiClient(
            refresh_token="fake_refresh_token", thread_pool=ThreadPoolExecutor(100)
        )
        self.test_ticker = Ticker(self.kfinance_api_client, "test")

    def company_object_keys_as_company_id(self, company_dict: Dict[Company, Any]):
        return dict(map(lambda company: (company.company_id, company_dict[company]), company_dict))

    @requests_mock.Mocker()
    def test_batch_request_property(self, m):
        """GIVEN a kfinance group object like Companies
        WHEN we batch request a property for each object in the group
        THEN the batch request completes successfully, and we get back a mapping of
        company objects to the corresponding values.

        Note: This test also checks that multiple tasks can be submitted. In the
        first implementation, we used the threadpool context manager, which shuts down
        the threadpool on __exit__ and prevented further tasks from getting submitted.
        """

        m.get(
            "https://kfinance.kensho.com/api/v1/info/1001",
            json={
                "name": "Mock Company A, Inc.",
                "city": "Mock City A",
            },
        )
        m.get(
            "https://kfinance.kensho.com/api/v1/info/1002",
            json={
                "name": "Mock Company B, Inc.",
                "city": "Mock City B",
            },
        )

        for _ in range(3):
            companies = Companies(self.kfinance_api_client, [1001, 1002])
            result = companies.city
            id_based_result = self.company_object_keys_as_company_id(result)

            expected_id_based_result = {1001: "Mock City A", 1002: "Mock City B"}
            self.assertDictEqual(id_based_result, expected_id_based_result)

    @requests_mock.Mocker()
    def test_batch_request_function(self, m):
        """GIVEN a kfinance group object like TradingItems
        WHEN we batch request a function for each object in the group
        THEN the batch request completes successfully and we get back a mapping of
        trading item objects to the corresponding values."""

        m.get(
            "https://kfinance.kensho.com/api/v1/pricing/2/none/none/day/adjusted",
            json={
                "currency": "USD",
                "prices": [
                    {
                        "date": "2024-04-11",
                        "open": "1.0000",
                        "high": "2.0000",
                        "low": "3.0000",
                        "close": "4.0000",
                        "volume": "5",
                    },
                ],
            },
        )
        m.get(
            "https://kfinance.kensho.com/api/v1/pricing/3/none/none/day/adjusted",
            json={
                "currency": "USD",
                "prices": [
                    {
                        "date": "2024-04-11",
                        "open": "5.0000",
                        "high": "6.0000",
                        "low": "7.0000",
                        "close": "8.0000",
                        "volume": "9",
                    },
                ],
            },
        )

        trading_item_2 = TradingItem(
            kfinance_api_client=self.kfinance_api_client, trading_item_id=2
        )
        trading_item_3 = TradingItem(
            kfinance_api_client=self.kfinance_api_client, trading_item_id=3
        )

        trading_items = TradingItems(
            self.kfinance_api_client, trading_items=[trading_item_2, trading_item_3]
        )
        expected_result = {
            trading_item_2: PriceHistory(
                prices=[
                    Prices(
                        date="2024-04-11",
                        open=Money(value=Decimal("1.00"), unit="USD", conventional_decimals=2),
                        high=Money(value=Decimal("2.00"), unit="USD", conventional_decimals=2),
                        low=Money(value=Decimal("3.00"), unit="USD", conventional_decimals=2),
                        close=Money(value=Decimal("4.00"), unit="USD", conventional_decimals=2),
                        volume=Shares(value=Decimal("5"), unit="Shares", conventional_decimals=0),
                    )
                ]
            ),
            trading_item_3: PriceHistory(
                prices=[
                    Prices(
                        date="2024-04-11",
                        open=Money(value=Decimal("5.00"), unit="USD", conventional_decimals=2),
                        high=Money(value=Decimal("6.00"), unit="USD", conventional_decimals=2),
                        low=Money(value=Decimal("7.00"), unit="USD", conventional_decimals=2),
                        close=Money(value=Decimal("8.00"), unit="USD", conventional_decimals=2),
                        volume=Shares(value=Decimal("9"), unit="Shares", conventional_decimals=0),
                    )
                ]
            ),
        }

        result = trading_items.history()
        assert result == expected_result

    @requests_mock.Mocker()
    def test_large_batch_request_property(self, m):
        """GIVEN a kfinance group object like Companies with a very large size
        WHEN we batch request a property for each object in the group
        THEN the batch request completes successfully and we get back a mapping of
        company objects to the corresponding values."""

        m.get(
            "https://kfinance.kensho.com/api/v1/info/1000",
            json={
                "name": "Test Inc.",
                "city": "Test City",
            },
        )

        BATCH_SIZE = 100
        companies = Companies(self.kfinance_api_client, [1000] * BATCH_SIZE)
        result = list(companies.city.values())
        expected_result = ["Test City"] * BATCH_SIZE
        self.assertEqual(result, expected_result)

    @requests_mock.Mocker()
    def test_batch_request_property_404(self, m):
        """GIVEN a kfinance group object like Companies
        WHEN we batch request a property for each object in the group and one of the
        property requests returns a 404
        THEN the batch request completes successfully and we get back a mapping of
        company objects to the corresponding property value or None when the request for
        that property returns a 404"""

        m.get(
            "https://kfinance.kensho.com/api/v1/info/1001",
            json={
                "name": "Mock Company A, Inc.",
                "city": "Mock City A",
            },
        )
        m.get("https://kfinance.kensho.com/api/v1/info/1002", status_code=404)

        companies = Companies(self.kfinance_api_client, [1001, 1002])
        result = companies.city
        id_based_result = self.company_object_keys_as_company_id(result)

        expected_id_based_result = {1001: "Mock City A", 1002: None}
        self.assertDictEqual(id_based_result, expected_id_based_result)

    @requests_mock.Mocker()
    def test_batch_request_400(self, m):
        """GIVEN a kfinance group object like Companies
        WHEN we batch request a property for each object in the group and one of the
        property requests returns a 400
        THEN the batch request returns a 400"""

        m.get(
            "https://kfinance.kensho.com/api/v1/info/1001",
            json={
                "name": "Mock Company A, Inc.",
                "city": "Mock City A",
            },
        )
        m.get("https://kfinance.kensho.com/api/v1/info/1002", status_code=400)

        with self.assertRaises(requests.exceptions.HTTPError) as e:
            companies = Companies(self.kfinance_api_client, [1001, 1002])
            _ = companies.city

        self.assertEqual(e.exception.response.status_code, 400)

    @requests_mock.Mocker()
    def test_batch_request_500(self, m):
        """GIVEN a kfinance group object like Companies
        WHEN we batch request a property for each object in the group and one of the
        property requests returns a 500
        THEN the batch request returns a 500"""

        m.get(
            "https://kfinance.kensho.com/api/v1/info/1001",
            json={
                "name": "Mock Company A, Inc.",
                "city": "Mock City A",
            },
        )
        m.get("https://kfinance.kensho.com/api/v1/info/1002", status_code=500)

        with self.assertRaises(requests.exceptions.HTTPError) as e:
            companies = Companies(self.kfinance_api_client, [1001, 1002])
            _ = companies.city

        self.assertEqual(e.exception.response.status_code, 500)

    @requests_mock.Mocker()
    def test_batch_request_property_with_thread_pool(self, m):
        """GIVEN a kfinance group object like Companies and an api client instantiated
        with a passed-in ThreadPool
        WHEN we batch request a property for each object in the group
        THEN the batch request completes successfully and we get back a mapping of
        company objects to corresponding values"""

        m.get(
            "https://kfinance.kensho.com/api/v1/info/1001",
            json={
                "name": "Mock Company A, Inc.",
                "city": "Mock City A",
            },
        )

        companies = Companies(self.kfinance_api_client_with_thread_pool, [1001])
        result = companies.city
        id_based_result = self.company_object_keys_as_company_id(result)

        expected_id_based_result = {1001: "Mock City A"}
        self.assertDictEqual(id_based_result, expected_id_based_result)

    @patch.object(Company, "info", new_callable=PropertyMock)
    def test_batch_requests_processed_in_parallel(self, mock_value: PropertyMock):
        """
        WHEN a batch request gets processed
        THEN the requests are handled in parallel not sequentially.
        """

        sleep_duration = 0.05

        def mock_info_with_sleep() -> dict[str, str]:
            """Mock an info call with a short sleep"""
            time.sleep(sleep_duration)
            return {"city": "Cambridge"}

        mock_value.side_effect = mock_info_with_sleep

        # Create tasks up to the MAX_WORKERS_CAP (max number of parallel tasks)
        companies = Companies(
            self.kfinance_api_client_with_thread_pool, [i for i in range(MAX_WORKERS_CAP)]
        )

        start = time.perf_counter()
        result = companies.city
        end = time.perf_counter()
        assert len(result) == MAX_WORKERS_CAP
        # Check that the requests run faster than sequential.
        # In practice, the requests should take barely more than the `sleep_duration` but timing
        # based tests can be flaky, especially in CI.
        assert end - start < MAX_WORKERS_CAP * sleep_duration
