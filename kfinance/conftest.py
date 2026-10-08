from datetime import datetime
from typing import Generator

import httpx2
import pytest
import respx
from respx import Route, Router

from kfinance.client.kfinance import Client
from kfinance.domains.companies.company_models import IdentificationTripleWithCompanyInfo


SPGI_COMPANY_ID = 21719
SPGI_SECURITY_ID = 2629107
SPGI_TRADING_ITEM_ID = 2629108
SPGI_COMPANY_NAME = "S&P Global Inc."
SPGI_TICKER = "NYSE:SPGI"
SPGI_COUNTRY = "USA"

SPGI_ID_TRIPLE = IdentificationTripleWithCompanyInfo(
    company_id=SPGI_COMPANY_ID,
    security_id=SPGI_SECURITY_ID,
    trading_item_id=SPGI_TRADING_ITEM_ID,
    company_name=SPGI_COMPANY_NAME,
    ticker=SPGI_TICKER,
    country=SPGI_COUNTRY,
)

FAKE_COMPANY_1_ID_TRIPLE = IdentificationTripleWithCompanyInfo(
    company_id=1,
    security_id=1,
    trading_item_id=1,
    company_name="Company 1",
    ticker="EXC:C1",
    country="USA",
)

FAKE_COMPANY_2_ID_TRIPLE = IdentificationTripleWithCompanyInfo(
    company_id=2,
    security_id=2,
    trading_item_id=2,
    company_name="Company 2",
    ticker="EXC:C2",
    country="USA",
)

NON_EXISTENT_ERROR = {
    "error": "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
}


def optional_route(route: Route) -> Route:
    """Allow a mocked route to go uncalled (the equivalent of pytest-httpx's is_optional=True)."""
    route.optional = True  # type: ignore[attr-defined]
    return route


@pytest.fixture
def httpx2_mock() -> Generator[Router, None, None]:
    """Mock all httpx2 requests.

    A request that matches no route fails the test, and so does a route that never gets
    called, unless it was wrapped in optional_route(). This overrides pytest-httpx2's
    fixture because respx's assert_all_called covers the whole router, so it can't make
    only some routes optional.
    """
    with respx.mock(using="httpcore2", assert_all_called=False) as router:
        yield router
        uncalled = [r for r in router.routes if not r.called and not getattr(r, "optional", False)]
        assert not uncalled, f"Mocked routes were never called: {uncalled}"


@pytest.fixture
def mock_client(httpx2_mock: Router) -> Client:
    """Create a KFinanceApiClient with a mock response for the SPGI id triple."""

    client = Client(refresh_token="foo")
    # Set access token so that the client doesn't try to fetch it.
    client.kfinance_api_client._access_token = "foo"  # noqa: SLF001
    client.kfinance_api_client._access_token_expiry = int(datetime(2100, 1, 1).timestamp())  # noqa: SLF001

    optional_route(httpx2_mock.get("https://kfinance.kensho.com/api/v1/id/SPGI")).respond(
        json=SPGI_ID_TRIPLE.model_dump(mode="json")
    )
    optional_route(httpx2_mock.get("https://kfinance.kensho.com/api/v1/id/MSFT")).respond(
        json={"trading_item_id": 2630413, "security_id": 2630412, "company_id": 21835}
    )

    # Create mock security id and trading item id for company ids 1 and 2:
    for company_id in [1, 2]:
        optional_route(
            httpx2_mock.get(f"https://kfinance.kensho.com/api/v1/securities/{company_id}/primary")
        ).respond(json={"primary_security": company_id})
        optional_route(
            httpx2_mock.get(
                f"https://kfinance.kensho.com/api/v1/trading_items/{company_id}/primary"
            )
        ).respond(json={"primary_trading_item": company_id})

    ids_url = "https://kfinance.kensho.com/api/v1/ids"
    ids_responses = {
        # Fetch SPGI
        ("SPGI",): {"SPGI": SPGI_ID_TRIPLE.model_dump(mode="json")},
        # Fetch a non-existent company (which will include an error)
        ("non-existent",): {"non-existent": NON_EXISTENT_ERROR},
        # Fetch a fake company
        ("C_1",): {"C_1": FAKE_COMPANY_1_ID_TRIPLE.model_dump(mode="json")},
        # Fetch SPGI and a non-existent company (which will include an error)
        ("SPGI", "non-existent"): {
            "SPGI": SPGI_ID_TRIPLE.model_dump(mode="json"),
            "non-existent": NON_EXISTENT_ERROR,
        },
        # Fetch SPGI and a private company (which will only have a company_id but no security or trading item id.)
        ("SPGI", "private_company"): {
            "SPGI": SPGI_ID_TRIPLE.model_dump(mode="json"),
            "private_company": {"company_id": 1, "security_id": None, "trading_item_id": None},
        },
        ("C_1", "C_2"): {
            "C_1": FAKE_COMPANY_1_ID_TRIPLE.model_dump(mode="json"),
            "C_2": FAKE_COMPANY_2_ID_TRIPLE.model_dump(mode="json"),
        },
    }
    for identifiers, data in ids_responses.items():
        optional_route(httpx2_mock.post(ids_url, json={"identifiers": list(identifiers)})).respond(
            json={"data": data}
        )

    return client


@pytest.fixture(scope="function")
def httpx_client(httpx2_mock: Router) -> httpx2.AsyncClient:
    """Create an async httpx client with mock responses for id resolution."""

    ids_url = "https://kfinance.kensho.com/api/v1/ids"
    ids_responses = {
        # Fetch SPGI
        ("SPGI",): {"SPGI": SPGI_ID_TRIPLE.model_dump(mode="json")},
        # Fetch non-existent company (only includes an error)
        ("non-existent",): {"non-existent": NON_EXISTENT_ERROR},
        # Fetch SPGI and a non-existent company (which will include an error)
        ("SPGI", "non-existent"): {
            "SPGI": SPGI_ID_TRIPLE.model_dump(mode="json"),
            "non-existent": NON_EXISTENT_ERROR,
        },
        # Fetch SPGI and a private company (which will only have a company_id but no security or trading item id.)
        ("SPGI", "private_company"): {
            "SPGI": SPGI_ID_TRIPLE.model_dump(mode="json"),
            "private_company": {
                "company_id": 1,
                "security_id": None,
                "trading_item_id": None,
                "company_name": "Private Company",
                "ticker": None,
                "country": "USA",
            },
        },
        # Fetch C_1 and C_2 (for multi-company testing)
        ("C_1", "C_2"): {
            "C_1": FAKE_COMPANY_1_ID_TRIPLE.model_dump(mode="json"),
            "C_2": FAKE_COMPANY_2_ID_TRIPLE.model_dump(mode="json"),
        },
    }
    for identifiers, data in ids_responses.items():
        optional_route(httpx2_mock.post(ids_url, json={"identifiers": list(identifiers)})).respond(
            json={"data": data}
        )

    return httpx2.AsyncClient(base_url="https://kfinance.kensho.com/api/v1")


@pytest.fixture
def add_spgi_supplier_mock_resp(httpx2_mock: Router) -> None:
    """Add mock response for SPGI supplier relationship."""
    httpx2_mock.get(
        f"https://kfinance.kensho.com/api/v1/relationship/{SPGI_COMPANY_ID}/supplier"
    ).respond(
        json={
            "current": [{"company_id": 883103, "company_name": "CRISIL Limited"}],
            "previous": [
                {"company_name": "Morgan Stanley", "company_id": 472898},
                {"company_name": "Eloqua, Inc.", "company_id": 8182358},
            ],
        }
    )
