from datetime import datetime

import httpx
import pytest
from pytest_httpx import HTTPXMock
from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.domains.companies.company_models import IdentificationTriple


SPGI_COMPANY_ID = 21719
SPGI_SECURITY_ID = 2629107
SPGI_TRADING_ITEM_ID = 2629108

SPGI_ID_TRIPLE = IdentificationTriple(
    company_id=SPGI_COMPANY_ID, security_id=SPGI_SECURITY_ID, trading_item_id=SPGI_TRADING_ITEM_ID
)


@pytest.fixture
def mock_client(requests_mock: Mocker) -> Client:
    """Create a KFinanceApiClient with a mock response for the SPGI id triple."""

    client = Client(refresh_token="foo")
    # Set access token so that the client doesn't try to fetch it.
    client.kfinance_api_client._access_token = "foo"  # noqa: SLF001
    client.kfinance_api_client._access_token_expiry = int(datetime(2100, 1, 1).timestamp())  # noqa: SLF001

    requests_mock.get(
        url="https://kfinance.kensho.com/api/v1/id/SPGI",
        json=SPGI_ID_TRIPLE.model_dump(mode="json"),
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
        json={"data": {"SPGI": SPGI_ID_TRIPLE.model_dump(mode="json")}},
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
    # Fetch a fake company
    requests_mock.post(
        url="https://kfinance.kensho.com/api/v1/ids",
        additional_matcher=lambda req: req.json().get("identifiers") == ["C_1"],
        json={
            "data": {
                "C_1": {"company_id": 1, "security_id": 1, "trading_item_id": 1},
            },
        },
    )
    # Fetch SPGI and a non-existent company (which will include an error)
    requests_mock.post(
        url="https://kfinance.kensho.com/api/v1/ids",
        additional_matcher=lambda req: req.json().get("identifiers") == ["SPGI", "non-existent"],
        json={
            "data": {
                "SPGI": SPGI_ID_TRIPLE.model_dump(mode="json"),
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
                "SPGI": SPGI_ID_TRIPLE.model_dump(mode="json"),
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


@pytest.fixture(scope="function")
def httpx_client(httpx_mock: HTTPXMock) -> httpx.AsyncClient:
    """Create an async httpx client with mock responses for id resolution."""

    # Fetch SPGI
    httpx_mock.add_response(
        url="https://kfinance.kensho.com/api/v1/ids",
        match_json={"identifiers": ["SPGI"]},
        json={"data": {"SPGI": SPGI_ID_TRIPLE.model_dump(mode="json")}},
        is_optional=True,
    )
    # Fetch non-existent company (only includes an error)
    httpx_mock.add_response(
        url="https://kfinance.kensho.com/api/v1/ids",
        match_json={"identifiers": ["non-existent"]},
        json={
            "data": {
                "non-existent": {
                    "error": "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                },
            }
        },
        is_optional=True,
    )
    # Fetch SPGI and a non-existent company (which will include an error)
    httpx_mock.add_response(
        url="https://kfinance.kensho.com/api/v1/ids",
        match_json={"identifiers": ["SPGI", "non-existent"]},
        json={
            "data": {
                "SPGI": SPGI_ID_TRIPLE.model_dump(mode="json"),
                "non-existent": {
                    "error": "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                },
            }
        },
        is_optional=True,
    )
    # Fetch SPGI and a private company (which will only have a company_id but no security or trading item id.)
    httpx_mock.add_response(
        url="https://kfinance.kensho.com/api/v1/ids",
        match_json={"identifiers": ["SPGI", "private_company"]},
        json={
            "data": {
                "SPGI": SPGI_ID_TRIPLE.model_dump(mode="json"),
                "private_company": {"company_id": 1, "security_id": None, "trading_item_id": None},
            }
        },
        is_optional=True,
    )
    # Fetch C_1 and C_2 (for multi-company testing)
    httpx_mock.add_response(
        url="https://kfinance.kensho.com/api/v1/ids",
        match_json={"identifiers": ["C_1", "C_2"]},
        json={
            "data": {
                "C_1": {"company_id": 1, "security_id": 1, "trading_item_id": 1},
                "C_2": {"company_id": 2, "security_id": 2, "trading_item_id": 2},
            }
        },
        is_optional=True,
    )

    return httpx.AsyncClient(base_url="https://kfinance.kensho.com/api/v1")
