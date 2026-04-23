from datetime import date, datetime, timezone
import json

import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.conftest import SPGI_COMPANY_ID, SPGI_ID_TRIPLE
from kfinance.domains.key_developments.key_devs_models import (
    KeyDevCategoryType,
    KeyDevelopment,
    KeyDevsResp,
)
from kfinance.domains.key_developments.key_devs_tools import (
    GetKeyDevsFromIdentifierResp,
    fetch_key_devs_from_company_id,
    get_key_devs_from_identifier,
)


@pytest.fixture
def add_spgi_key_devs_mock_resp(httpx_mock: HTTPXMock) -> None:
    """Add mock response for SPGI key developments."""
    httpx_mock.add_response(
        method="POST",
        url="https://kfinance.kensho.com/api/v1/key_devs",
        json={
            "results": {
                "Client Announcements": [
                    {
                        "key_dev_id": 1001,
                        "situation": "S&P Global announces new partnership",
                        "announced_date_utc": "2025-03-15T14:30:00Z",
                        "most_important_date_utc": "2025-03-15T14:30:00Z",
                        "source": "Press Release",
                        "company_role": "Subject",
                    }
                ],
                "Earnings Releases": [
                    {
                        "key_dev_id": 1002,
                        "situation": "S&P Global reports Q1 2025 earnings",
                        "announced_date_utc": "2025-04-29T12:00:00Z",
                        "most_important_date_utc": "2025-04-29T12:00:00Z",
                        "source": "Company Report",
                        "company_role": "Subject",
                    }
                ],
            },
            "next_time_band": None,
            "notes": None,
        },
        is_optional=True,
    )


class TestKeyDevs:
    expected_spgi_key_devs_response = KeyDevsResp(
        results={
            "Client Announcements": [
                KeyDevelopment(
                    key_dev_id=1001,
                    situation="S&P Global announces new partnership",
                    announced_date_utc=datetime(2025, 3, 15, 14, 30, 0, tzinfo=timezone.utc),
                    most_important_date_utc=datetime(2025, 3, 15, 14, 30, 0, tzinfo=timezone.utc),
                    source="Press Release",
                    company_role="Subject",
                )
            ],
            "Earnings Releases": [
                KeyDevelopment(
                    key_dev_id=1002,
                    situation="S&P Global reports Q1 2025 earnings",
                    announced_date_utc=datetime(2025, 4, 29, 12, 0, 0, tzinfo=timezone.utc),
                    most_important_date_utc=datetime(2025, 4, 29, 12, 0, 0, tzinfo=timezone.utc),
                    source="Company Report",
                    company_role="Subject",
                )
            ],
        },
        next_time_band=None,
        notes=None,
    )

    @pytest.mark.asyncio
    async def test_fetch_key_devs_from_company_id(
        self, httpx_client: httpx.AsyncClient, add_spgi_key_devs_mock_resp: None
    ) -> None:
        """
        WHEN we request SPGI's key developments (using SPGI's company id)
        THEN we get back SPGI's key developments.
        """

        resp = await fetch_key_devs_from_company_id(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
        )
        assert resp == self.expected_spgi_key_devs_response

    @pytest.mark.asyncio
    async def test_fetch_key_devs_with_date_range(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN we request key developments with a date range
        THEN the request includes start_date and end_date parameters.
        """
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/key_devs",
            json={"results": {}, "next_time_band": None, "notes": None},
        )

        await fetch_key_devs_from_company_id(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )

        # verify the request was made with correct payload
        request = httpx_mock.get_request()
        assert request is not None

        payload = json.loads(request.content)
        assert payload["company_id"] == SPGI_COMPANY_ID
        assert payload["start_date"] == "2025-01-01"
        assert payload["end_date"] == "2025-12-31"

    @pytest.mark.asyncio
    async def test_fetch_key_devs_with_category_filter(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN we request key developments with a category filter
        THEN the request includes key_dev_category parameter.
        """

        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/key_devs",
            json={"results": {}, "next_time_band": None, "notes": None},
        )

        await fetch_key_devs_from_company_id(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            key_dev_category=KeyDevCategoryType.ANNOUNCED_OR_COMPLETED_TRANSACTIONS,
        )

        # verify the request was made with correct payload
        request = httpx_mock.get_request()
        assert request is not None

        payload = json.loads(request.content)
        assert payload["company_id"] == SPGI_COMPANY_ID
        assert payload["key_dev_category"] == 2

    @pytest.mark.asyncio
    async def test_get_key_devs_from_identifier(
        self, httpx_client: httpx.AsyncClient, add_spgi_key_devs_mock_resp: None
    ) -> None:
        """
        WHEN we fetch key developments for SPGI and a non-existent company
        THEN we get back SPGI's key developments and an error for the non-existent company.
        """

        expected_resp = GetKeyDevsFromIdentifierResp(
            identifier_results={"SPGI": self.expected_spgi_key_devs_response},
            identifier_info={"SPGI": SPGI_ID_TRIPLE},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )

        resp = await get_key_devs_from_identifier(
            identifier="SPGI",
            httpx_client=httpx_client,
        )

        # test with non-existent identifier separately to capture error
        resp_with_error = await get_key_devs_from_identifier(
            identifier="non-existent",
            httpx_client=httpx_client,
        )

        # combine results for comparison
        combined_resp = GetKeyDevsFromIdentifierResp(
            identifier_results=resp.identifier_results,
            identifier_info=resp.identifier_info,
            errors=resp.errors + resp_with_error.errors,
        )

        assert combined_resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_key_devs_with_api_error(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN the key devs API returns an error (e.g. no data available)
        THEN the error is extracted and surfaced in the response
        """
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/key_devs",
            json={
                "results": {},
                "next_time_band": None,
                "notes": None,
                "errors": [f"There is no data associated with company id {SPGI_COMPANY_ID}"],
            },
        )

        expected_resp = GetKeyDevsFromIdentifierResp(
            identifier_results={},
            identifier_info={"SPGI": SPGI_ID_TRIPLE},
            errors=[f"SPGI: There is no data associated with company id {SPGI_COMPANY_ID}"],
        )

        resp = await get_key_devs_from_identifier(
            identifier="SPGI",
            httpx_client=httpx_client,
        )

        assert resp == expected_resp
