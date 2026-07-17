from datetime import datetime, timezone

import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.domains.ratings.ratings_models import (
    EntityInfo,
    IssuerRatings,
    RatingDetail,
    RatingTypeData,
)
from kfinance.domains.ratings.ratings_tools import (
    GetIssuerRatingsFromIdentifiersResp,
    fetch_issuer_ratings_from_identifiers,
    get_issuer_ratings_from_identifiers,
)


# Mock entity info for SPGI
SPGI_ENTITY_INFO = EntityInfo(
    entity_id=21719,
    entity_name="S&P Global Inc.",
    ticker="NYSE:SPGI",
    country="USA",
)


@pytest.fixture
def add_spgi_resolve_entities_mock_resp(httpx_mock: HTTPXMock) -> None:
    """Add mock response for resolving SPGI identifier."""
    httpx_mock.add_response(
        method="POST",
        url="https://kfinance.kensho.com/api/v1/ratings/resolve_entities/",
        json={
            "data": {
                "SPGI": {
                    "entity_id": 21719,
                    "entity_name": "S&P Global Inc.",
                    "ticker": "NYSE:SPGI",
                    "country": "USA",
                },
                "non-existent": {
                    "error": "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                },
            }
        },
        is_optional=True,
    )


@pytest.fixture
def add_spgi_ratings_mock_resp(httpx_mock: HTTPXMock) -> None:
    """Add mock response for SPGI issuer ratings."""
    httpx_mock.add_response(
        method="POST",
        url="https://kfinance.kensho.com/api/v1/ratings/issuer_ratings/",
        json={
            "results": {
                "21719": {
                    "ratings": {
                        "ICR": {
                            "FCLONG": {
                                "source": "S&P Global",
                                "last_review_date": "2025-05-22T01:13:55Z",
                                "latest": {
                                    "rating": "AA+",
                                    "rating_datetime": "2013-04-23T16:35:10Z",
                                    "rating_action_word": "New Rating",
                                    "credit_watch": None,
                                    "credit_watch_datetime": None,
                                    "outlook": "Stable",
                                    "outlook_datetime": "2013-04-23T16:35:10Z",
                                },
                                "history": [],
                            }
                        }
                    }
                }
            },
            "errors": {},
        },
        is_optional=True,
    )


class TestRatings:
    expected_spgi_ratings_response = IssuerRatings(
        ratings={
            "ICR": {
                "FCLONG": RatingTypeData(
                    source="S&P Global",
                    last_review_date=datetime(2025, 5, 22, 1, 13, 55, tzinfo=timezone.utc),
                    latest=RatingDetail(
                        rating="AA+",
                        rating_datetime=datetime(2013, 4, 23, 16, 35, 10, tzinfo=timezone.utc),
                        rating_action_word="New Rating",
                        credit_watch=None,
                        credit_watch_datetime=None,
                        outlook="Stable",
                        outlook_datetime=datetime(2013, 4, 23, 16, 35, 10, tzinfo=timezone.utc),
                    ),
                    history=[],
                )
            }
        }
    )

    @pytest.mark.asyncio
    async def test_fetch_issuer_ratings_from_identifiers(
        self, httpx_client: httpx.AsyncClient, add_spgi_ratings_mock_resp: None
    ) -> None:
        """
        WHEN we request SPGI's issuer ratings (using entity_id)
        THEN we get back SPGI's ratings.
        """

        resp = await fetch_issuer_ratings_from_identifiers(
            entity_ids=[21719],
            httpx_client=httpx_client,
        )

        assert resp.results["21719"] == self.expected_spgi_ratings_response
        assert resp.errors == {}

    @pytest.mark.asyncio
    async def test_get_issuer_ratings_from_identifiers(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_resolve_entities_mock_resp: None,
        add_spgi_ratings_mock_resp: None,
    ) -> None:
        """
        WHEN we request ratings for SPGI and a non-existent identifier
        THEN we get back SPGI's ratings and an error for the non-existent identifier.
        """

        expected_resp = GetIssuerRatingsFromIdentifiersResp.create(
            identifier_results={"SPGI": self.expected_spgi_ratings_response},
            identifier_info={"SPGI": SPGI_ENTITY_INFO},
            errors=[
                "non-existent: No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )

        resp = await get_issuer_ratings_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            httpx_client=httpx_client,
        )

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_issuer_ratings_with_api_error(
        self,
        httpx_client: httpx.AsyncClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """
        WHEN the ratings API returns an error
        THEN the error is mapped back to the identifier and included in the response.
        """
        # Mock entity resolution
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/ratings/resolve_entities/",
            json={
                "data": {
                    "SPGI": {
                        "entity_id": 21719,
                        "entity_name": "S&P Global Inc.",
                        "ticker": "NYSE:SPGI",
                        "country": "USA",
                    }
                }
            },
        )

        # Mock ratings API error
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/ratings/issuer_ratings/",
            json={
                "results": {},
                "errors": {"21719": "No ratings data available"},
            },
        )

        expected_resp = GetIssuerRatingsFromIdentifiersResp.create(
            identifier_results={},
            identifier_info={},
            errors=["SPGI: No ratings data available"],
        )

        resp = await get_issuer_ratings_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
        )

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_all_identifiers_fail_resolution(
        self,
        httpx_client: httpx.AsyncClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """
        WHEN all identifiers fail resolution
        THEN we get back an empty results dict and errors.
        """
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/ratings/resolve_entities/",
            json={
                "data": {
                    "non-existent": {
                        "error": "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                    }
                }
            },
        )

        expected_resp = GetIssuerRatingsFromIdentifiersResp.create(
            identifier_results={},
            identifier_info={},
            errors=[
                "non-existent: No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )

        resp = await get_issuer_ratings_from_identifiers(
            identifiers=["non-existent"],
            httpx_client=httpx_client,
        )

        assert resp == expected_resp
