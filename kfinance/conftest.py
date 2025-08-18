from datetime import datetime

import pytest
from requests_mock import Mocker

from kfinance.client.kfinance import Client


SPGI_COMPANY_ID = 21719
SPGI_SECURITY_ID = 2629107
SPGI_TRADING_ITEM_ID = 2629108


@pytest.fixture
def mock_client(requests_mock: Mocker) -> Client:
    """Create a KFinanceApiClient with a mock response for the SPGI id triple."""

    client = Client(refresh_token="foo")
    # Set access token so that the client doesn't try to fetch it.
    client.kfinance_api_client._access_token = "foo"  # noqa: SLF001
    client.kfinance_api_client._access_token_expiry = int(datetime(2100, 1, 1).timestamp())  # noqa: SLF001

    # Create a mock for the SPGI id triple.
    spgi_id_triple = {
        "trading_item_id": SPGI_TRADING_ITEM_ID,
        "security_id": SPGI_SECURITY_ID,
        "company_id": SPGI_COMPANY_ID,
    }
    requests_mock.get(
        url="https://kfinance.kensho.com/api/v1/id/SPGI",
        json=spgi_id_triple,
    )
    requests_mock.get(
        url="https://kfinance.kensho.com/api/v1/id/MSFT",
        json={"trading_item_id": 2630413, "security_id": 2630412, "company_id": 21835},
    )

    # Create mock security id and trading item id for company ids 1 and 2:
    for company_id in [1, 2]:
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/securities/{company_id}/primary",
            json={"primary_security": company_id},
        )
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/trading_items/{company_id}/primary",
            json={"primary_trading_item": company_id},
        )

    # Fetch SPGI
    requests_mock.post(
        url="https://kfinance.kensho.com/api/v1/ids",
        additional_matcher=lambda req: req.json().get("identifiers") == ["SPGI"],
        json={"data": {"SPGI": spgi_id_triple}},
    )
    # Fetch a non-existent company (which will include an error)
    requests_mock.post(
        url="https://kfinance.kensho.com/api/v1/ids",
        additional_matcher=lambda req: req.json().get("identifiers") == ["non-existent"],
        json={
            "data": {
                "non-existent": {
                    "error": "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                },
            }
        },
    )
    # Fetch SPGI and a non-existent company (which will include an error)
    requests_mock.post(
        url="https://kfinance.kensho.com/api/v1/ids",
        additional_matcher=lambda req: req.json().get("identifiers") == ["SPGI", "non-existent"],
        json={
            "data": {
                "SPGI": spgi_id_triple,
                "non-existent": {
                    "error": "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                },
            }
        },
    )
    # Fetch SPGI and a private company (which will only have a company_id but no security or trading item id.)
    requests_mock.post(
        url="https://kfinance.kensho.com/api/v1/ids",
        additional_matcher=lambda req: req.json().get("identifiers") == ["SPGI", "private_company"],
        json={
            "data": {
                "SPGI": spgi_id_triple,
                "private_company": {"company_id": 1, "security_id": None, "trading_item_id": None},
            }
        },
    )

    requests_mock.post(
        url="https://kfinance.kensho.com/api/v1/ids",
        additional_matcher=lambda req: req.json().get("identifiers") == ["C_1", "C_2"],
        json={
            "data": {
                "C_1": {"company_id": 1, "security_id": 1, "trading_item_id": 1},
                "C_2": {"company_id": 2, "security_id": 2, "trading_item_id": 2},
            }
        },
    )

    return client
