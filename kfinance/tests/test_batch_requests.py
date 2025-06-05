from concurrent.futures import ThreadPoolExecutor
import time
from typing import Any, Dict
from unittest import TestCase
from unittest.mock import PropertyMock, patch

import numpy as np
import pandas as pd
import pytest
import requests
import requests_mock

from kfinance.batch_request_handling import MAX_WORKERS_CAP
from kfinance.fetch import KFinanceApiClient
from kfinance.kfinance import Companies, Company, Ticker, TradingItems


@pytest.fixture(autouse=True)
def mock_method():
    with patch("kfinance.fetch.KFinanceApiClient.access_token", return_value="fake_access_token"):
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
                "prices": [
                    {"date": "2024-01-01", "close": "100.000000"},
                    {"date": "2024-01-02", "close": "101.000000"},
                ]
            },
        )
        m.get(
            "https://kfinance.kensho.com/api/v1/pricing/3/none/none/day/adjusted",
            json={
                "prices": [
                    {"date": "2024-01-01", "close": "200.000000"},
                    {"date": "2024-01-02", "close": "201.000000"},
                ]
            },
        )

        trading_items = TradingItems(self.kfinance_api_client, [2, 3])

        result = trading_items.history()
        expected_dictionary_based_result = {
            2: [
                {"date": "2024-01-01", "close": "100.000000"},
                {"date": "2024-01-02", "close": "101.000000"},
            ],
            3: [
                {"date": "2024-01-01", "close": "200.000000"},
                {"date": "2024-01-02", "close": "201.000000"},
            ],
        }
        self.assertEqual(len(result), len(expected_dictionary_based_result))

        for k, v in result.items():
            trading_item_id = k.trading_item_id
            pd.testing.assert_frame_equal(
                v,
                pd.DataFrame(expected_dictionary_based_result[trading_item_id])
                .set_index("date")
                .apply(pd.to_numeric)
                .replace(np.nan, None),
            )

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
