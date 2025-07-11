from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_COMPANY_ID
from kfinance.domains.capitalizations.capitalization_models import Capitalization
from kfinance.domains.capitalizations.capitalization_tools import (
    GetCapitalizationFromIdentifiers,
    GetCapitalizationFromIdentifiersArgs,
)
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX


class TestGetCapitalizationFromCompanyIds:
    market_caps_resp = {
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

    def test_get_capitalization_from_identifiers(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetCapitalizationFromIdentifiers tool
        WHEN we request the SPGI market cap
        THEN we get back the SPGI market cap
        """
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/market_cap/{SPGI_COMPANY_ID}/none/none",
            json=self.market_caps_resp,
        )

        expected_response = {
            "SPGI": [
                {"date": "2024-04-10", "market_cap": {"unit": "USD", "value": "132766738270.00"}},
                {"date": "2024-04-11", "market_cap": {"unit": "USD", "value": "132416066761.00"}},
            ]
        }

        tool = GetCapitalizationFromIdentifiers(kfinance_client=mock_client)
        args = GetCapitalizationFromIdentifiersArgs(
            identifiers=["SPGI"], capitalization=Capitalization.market_cap
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetCapitalizationFromIdentifiers tool
        WHEN we request most recent market caps for multiple companies
        THEN we only get back the most recent market cap for each company
        """
        expected_response = {
            "C_1": [
                {"date": "2024-04-10", "market_cap": {"unit": "USD", "value": "132766738270.00"}}
            ],
            "C_2": [
                {"date": "2024-04-10", "market_cap": {"unit": "USD", "value": "132766738270.00"}}
            ],
        }

        company_ids = [1, 2]
        for company_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/market_cap/{company_id}/none/none",
                json=self.market_caps_resp,
            )
        tool = GetCapitalizationFromIdentifiers(kfinance_client=mock_client)
        args = GetCapitalizationFromIdentifiersArgs(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            capitalization=Capitalization.market_cap,
        )

        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response
