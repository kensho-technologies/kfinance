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
        self.test_ticker = Ticker(self.kfinance_api_client, "test")

    def company_object_keys_as_company_id(self, company_dict: Dict[Company, Any]):
        return dict(map(lambda company: (company.company_id, company_dict[company]), company_dict))

    @requests_mock.Mocker()
    def test_batch_request_property(self, m):
        """Test batch request property and 404"""
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
        formatted_result = self.company_object_keys_as_company_id(result)

        # company with company id 1005 raises a 404 error on the info route, so its corresponding value should be None
        expected_result = {1001: "Mock City A", 1002: "Mock City B"}
        self.assertDictEqual(formatted_result, expected_result)

    @requests_mock.Mocker()
    def test_batch_request_cached_properties(self, m):
        """Test batch request cached property."""
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

        formatted_result = self.company_object_keys_as_company_id(result)
        for k, v in formatted_result.items():
            formatted_result[k] = set(map(lambda s: s.security_id, v))

        expected_result = {
            1001: set([101, 102, 103]),
            1002: set([104, 105, 106, 107]),
            1005: set([108, 109]),
        }

        self.assertDictEqual(formatted_result, expected_result)

    @requests_mock.Mocker()
    def test_batch_request_function(self, m):
        """Test batch request history function."""
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
        expected_result = {
            2: [
                {"date": "2024-01-01", "close": "100.000000"},
                {"date": "2024-01-02", "close": "101.000000"},
            ],
            3: [
                {"date": "2024-01-01", "close": "200.000000"},
                {"date": "2024-01-02", "close": "201.000000"},
            ],
        }
        self.assertEqual(len(result), len(expected_result))

        for k, v in result.items():
            trading_item_id = k.trading_item_id
            pd.testing.assert_frame_equal(
                v,
                pd.DataFrame(expected_result[trading_item_id])
                .set_index("date")
                .apply(pd.to_numeric)
                .replace(np.nan, None),
            )

    @requests_mock.Mocker()
    def test_large_batch_request_property(self, m):
        """test business relationship large batch request property."""
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
        """Test batch request property and 404"""
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
        formatted_result = self.company_object_keys_as_company_id(result)

        # the company with company id 1002 raises a 404 error on the info route, so its corresponding value should be None
        expected_result = {1001: "Mock City A", 1002: None}
        self.assertDictEqual(formatted_result, expected_result)

    @requests_mock.Mocker()
    def test_batch_request_400(self, m):
        """test batch request property where one instance returns a 400"""
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
        """test batch request property where one instance returns a 400"""
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
