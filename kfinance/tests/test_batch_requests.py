from typing import Any, Dict
from unittest import TestCase
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
import requests
import requests_mock

from kfinance.fetch import KFinanceApiClient
from kfinance.kfinance import Companies, Company, Ticker


MOCK_RESPONSES = {
    "https://kfinance.kensho.com/api/v1/id/test": {
        "trading_item_id": 1,
        "security_id": 100,
        "company_id": 1000,
    },
    "https://kfinance.kensho.com/api/v1/relationship/1000/distributor": {
        "current": [1001, 1002, 1005],
        "previous": [1003, 1004],
    },
    "https://kfinance.kensho.com/api/v1/securities/1001": {"securities": [101, 102, 103]},
    "https://kfinance.kensho.com/api/v1/securities/1002": {"securities": [104, 105, 106, 107]},
    "https://kfinance.kensho.com/api/v1/securities/1005": {"securities": [108, 109]},
    "https://kfinance.kensho.com/api/v1/info/1000": {
        "name": "Test Inc.",
        "city": "Test City",
    },
    "https://kfinance.kensho.com/api/v1/info/1001": {
        "name": "Mock Company A, Inc.",
        "city": "Mock City A",
    },
    "https://kfinance.kensho.com/api/v1/info/1002": {
        "name": "Mock Company B, Inc.",
        "city": "Mock City B",
    },
    "https://kfinance.kensho.com/api/v1/info/1003": {
        "name": "Mock Company C, Inc.",
        "city": "Mock City C",
    },
    "https://kfinance.kensho.com/api/v1/trading_items/100": {"trading_items": [2, 3]},
    "https://kfinance.kensho.com/api/v1/pricing/2/none/none/day/adjusted": {
        "prices": [
            {"date": "2024-01-01", "close": "100.000000"},
            {"date": "2024-01-02", "close": "101.000000"},
        ]
    },
    "https://kfinance.kensho.com/api/v1/pricing/3/none/none/day/adjusted": {
        "prices": [
            {"date": "2024-01-01", "close": "200.000000"},
            {"date": "2024-01-02", "close": "201.000000"},
        ]
    },
}

MOCK_EXCEPTIONS = {
    "https://kfinance.kensho.com/api/v1/info/1004": 400,
    "https://kfinance.kensho.com/api/v1/info/1005": 404,
}


@pytest.fixture(autouse=True)
def mock_method():
    with patch("kfinance.fetch.KFinanceApiClient.access_token", return_value="fake_access_token"):
        yield


@requests_mock.Mocker()
class TestTradingItem(TestCase):
    def setUp(self):
        self.kfinance_api_client = KFinanceApiClient(refresh_token="fake_refresh_token")
        self.test_ticker = Ticker(self.kfinance_api_client, "test")

    def _setup_mock_responses(self, m):
        """Helper method to set up all mock responses."""
        for url, response_data in MOCK_RESPONSES.items():
            m.get(url, json=response_data)
        for url, status_code in MOCK_EXCEPTIONS.items():
            m.get(url, status_code=status_code)

    def change_company_object_keys_to_company_id(self, company_dict: Dict[Company, Any]):
        for company in company_dict:
            value = company_dict[company]
            del company_dict[company]
            company_dict[company.company_id] = value

    def test_batch_request_property_and_404(self, m):
        """Test batch request property and 404"""
        self._setup_mock_responses(m)

        result = self.test_ticker.company.distributor.current.city
        # company with company id 1005 raises a 404 error on the info route, so its corresponding value should be None
        self.change_company_object_keys_to_company_id(result)

        expected_result = {1001: "Mock City A", 1002: "Mock City B", 1005: None}
        self.assertDictEqual(result, expected_result)

    def test_batch_request_cached_properties(self, m):
        """Test batch request cached property."""
        self._setup_mock_responses(m)

        result = self.test_ticker.company.distributor.current.securities

        self.change_company_object_keys_to_company_id(result)
        for k, v in result.items():
            result[k] = list(map(lambda s: s.security_id, v))

        expected_result = {1001: [101, 102, 103], 1002: [104, 105, 106, 107], 1005: [108, 109]}

        self.assertDictEqual(result, expected_result)

    def test_batch_request_function(self, m):
        """Test batch request history function."""
        self._setup_mock_responses(m)

        result = self.test_ticker.primary_security.trading_items.history()
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

    def test_large_batch_request_property(self, m):
        """test business relationship large batch request property."""
        self._setup_mock_responses(m)

        BATCH_SIZE = 100
        companies = Companies(self.kfinance_api_client, [self.test_ticker.company_id] * BATCH_SIZE)
        result = list(companies.city.values())
        expected_result = ["Test City"] * BATCH_SIZE
        self.assertEqual(result, expected_result)

    def test_batch_request_400(self, m):
        """test batch request property where one instance returns a 400"""
        self._setup_mock_responses(m)

        with self.assertRaises(requests.exceptions.HTTPError):
            _ = self.test_ticker.company.distributor.previous.city
