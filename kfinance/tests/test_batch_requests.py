from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict
from unittest import TestCase
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
import requests
import requests_mock

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
        THEN the batch request completes successfully and we get back a mapping of
        company objects to the corresponding values."""

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

        companies = Companies(self.kfinance_api_client, [1001, 1002])
        result = companies.city
        id_based_result = self.company_object_keys_as_company_id(result)

        expected_id_based_result = {1001: "Mock City A", 1002: "Mock City B"}
        self.assertDictEqual(id_based_result, expected_id_based_result)

    @requests_mock.Mocker()
    def test_batch_request_cached_properties(self, m):
        """GIVEN a kfinance group object like Companies
        WHEN we batch request a cached property for each object in the group
        THEN the batch request completes successfully and we get back a mapping of
        company objects to the corresponding values."""

        m.get(
            "https://kfinance.kensho.com/api/v1/securities/1001",
            json={"securities": [101, 102, 103]},
        )
        m.get(
            "https://kfinance.kensho.com/api/v1/securities/1002",
            json={"securities": [104, 105, 106, 107]},
        )
        m.get("https://kfinance.kensho.com/api/v1/securities/1005", json={"securities": [108, 109]})

        companies = Companies(self.kfinance_api_client, [1001, 1002, 1005])
        result = companies.securities

        id_based_result = self.company_object_keys_as_company_id(result)
        for k, v in id_based_result.items():
            id_based_result[k] = set(map(lambda s: s.security_id, v))

        expected_id_based_result = {
            1001: set([101, 102, 103]),
            1002: set([104, 105, 106, 107]),
            1005: set([108, 109]),
        }

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
