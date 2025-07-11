from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_TRADING_ITEM_ID
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX
from kfinance.domains.prices.price_tools import (
    GetHistoryMetadataFromIdentifiers,
    GetPricesFromIdentifiers,
    GetPricesFromIdentifiersArgs,
)
from kfinance.integrations.tool_calling.tool_calling_models import ToolArgsWithIdentifiers


class TestGetHistoryMetadataFromIdentifiers:
    def test_get_history_metadata_from_identifiers(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN the GetHistoryMetadataFromIdentifiers tool
        WHEN we request the history metadata for SPGI
        THEN we get back SPGI's history metadata
        """
        metadata_resp = {
            "currency": "USD",
            "exchange_name": "NYSE",
            "first_trade_date": "1968-01-02",
            "instrument_type": "Equity",
            "symbol": "SPGI",
        }
        expected_resp = {"SPGI": metadata_resp}

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/pricing/{SPGI_TRADING_ITEM_ID}/metadata",
            json=metadata_resp,
        )

        tool = GetHistoryMetadataFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run(ToolArgsWithIdentifiers(identifiers=["SPGI"]).model_dump(mode="json"))
        assert resp == expected_resp


class TestPricesFromIdentifiers:
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

    def test_get_prices_from_identifiers(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetPricesFromIdentifiers tool
        WHEN we request prices for SPGI
        THEN we get back prices for SPGI
        """

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/pricing/{SPGI_TRADING_ITEM_ID}/none/none/day/adjusted",
            json=self.prices_resp,
        )
        expected_response = {
            "SPGI": {
                "prices": [
                    {
                        "date": "2024-04-11",
                        "open": {"value": "424.26", "unit": "USD"},
                        "high": {"value": "425.99", "unit": "USD"},
                        "low": {"value": "422.04", "unit": "USD"},
                        "close": {"value": "422.92", "unit": "USD"},
                        "volume": {"value": "1129158", "unit": "Shares"},
                    },
                    {
                        "date": "2024-04-12",
                        "open": {"value": "419.23", "unit": "USD"},
                        "high": {"value": "421.94", "unit": "USD"},
                        "low": {"value": "416.45", "unit": "USD"},
                        "close": {"value": "417.81", "unit": "USD"},
                        "volume": {"value": "1182229", "unit": "Shares"},
                    },
                ]
            }
        }

        tool = GetPricesFromIdentifiers(kfinance_client=mock_client)
        response = tool.run(
            GetPricesFromIdentifiersArgs(identifiers=["SPGI"]).model_dump(mode="json")
        )
        assert response == expected_response

    def test_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetPricesFromIdentifiers tool
        WHEN we request most recent prices for multiple companies
        THEN we only get back the most recent prices for each company
        """

        company_ids = [1, 2]
        for trading_item_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/pricing/{trading_item_id}/none/none/day/adjusted",
                json=self.prices_resp,
            )

        expected_single_company_response = {
            "prices": [
                {
                    "date": "2024-04-11",
                    "open": {"value": "424.26", "unit": "USD"},
                    "high": {"value": "425.99", "unit": "USD"},
                    "low": {"value": "422.04", "unit": "USD"},
                    "close": {"value": "422.92", "unit": "USD"},
                    "volume": {"value": "1129158", "unit": "Shares"},
                }
            ]
        }
        expected_response = {
            "C_1": expected_single_company_response,
            "C_2": expected_single_company_response,
        }
        tool = GetPricesFromIdentifiers(kfinance_client=mock_client)
        response = tool.run(
            GetPricesFromIdentifiersArgs(
                identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids]
            ).model_dump(mode="json")
        )
        assert response == expected_response
