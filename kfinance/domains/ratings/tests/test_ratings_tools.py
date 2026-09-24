from datetime import datetime, timezone

import httpx2
import pytest

from kfinance.domains.ratings.ratings_models import (
    EntityInfo,
    IssuerRatings,
    IssuerRatingTypeData,
    RatingDetail,
    RatingTypeData,
    SecurityRatings,
)
from kfinance.domains.ratings.ratings_tools import (
    GetIssuerRatingsFromIdentifiersResp,
    GetSecurityRatingsFromIdentifiersResp,
    fetch_issuer_ratings_from_identifiers,
    fetch_security_ratings_from_identifiers,
    get_issuer_ratings_from_identifiers,
    get_security_ratings_from_identifiers,
)


# Mock entity info for SPGI
SPGI_ENTITY_INFO = EntityInfo(
    entity_id=21719,
    entity_name="S&P Global Inc.",
    ticker="NYSE:SPGI",
    country="USA",
)


@pytest.fixture
def add_spgi_resolve_entities_mock_resp(httpx2_mock) -> None:
    """Add mock response for resolving SPGI identifier."""
    httpx2_mock.post("https://kfinance.kensho.com/api/v1/ratings/resolve_entities/").respond(
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
        }
    )


@pytest.fixture
def add_spgi_ratings_mock_resp(httpx2_mock) -> None:
    """Add mock response for SPGI issuer ratings."""
    httpx2_mock.post("https://kfinance.kensho.com/api/v1/ratings/issuer_ratings/").respond(
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
        }
    )


@pytest.fixture
def add_security_ratings_mock_resp(httpx2_mock) -> None:
    """Add mock response for security ratings."""
    httpx2_mock.post("https://kfinance.kensho.com/api/v1/ratings/security_ratings/").respond(
        json={
            "results": {
                "123456789": {
                    "ciq_security_id": 123456789,
                    "ratings": {
                        "FCLONG": {
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
                            "source": "S&P Global",
                        }
                    },
                }
            },
            "errors": {},
        }
    )


class TestRatings:
    expected_spgi_ratings_response = IssuerRatings(
        ratings={
            "ICR": {
                "FCLONG": IssuerRatingTypeData(
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
        self, httpx_client: httpx2.AsyncClient, add_spgi_ratings_mock_resp: None
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
        httpx_client: httpx2.AsyncClient,
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
        httpx_client: httpx2.AsyncClient,
        httpx2_mock,
    ) -> None:
        """
        WHEN the ratings API returns an error
        THEN the error identifies what the original identifier resolved to.
        """
        # Mock entity resolution
        httpx2_mock.post("https://kfinance.kensho.com/api/v1/ratings/resolve_entities/").respond(
            json={
                "data": {
                    "USA": {
                        "entity_id": 4217533,
                        "entity_name": "United States",
                        "ticker": None,
                        "country": "USA",
                    }
                }
            }
        )

        # Mock ratings API error
        httpx2_mock.post("https://kfinance.kensho.com/api/v1/ratings/issuer_ratings/").respond(
            json={
                "results": {},
                "errors": {"4217533": "No results found."},
            }
        )

        expected_resp = GetIssuerRatingsFromIdentifiersResp.create(
            identifier_results={},
            identifier_info={},
            errors=[
                "USA: No ratings data found for entity which resolved to United States "
                "(entity ID 4217533)."
            ],
        )

        resp = await get_issuer_ratings_from_identifiers(
            identifiers=["USA"],
            httpx_client=httpx_client,
        )

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_all_identifiers_fail_resolution(
        self,
        httpx_client: httpx2.AsyncClient,
        httpx2_mock,
    ) -> None:
        """
        WHEN all identifiers fail resolution
        THEN we get back an empty results dict and errors.
        """
        httpx2_mock.post("https://kfinance.kensho.com/api/v1/ratings/resolve_entities/").respond(
            json={
                "data": {
                    "non-existent": {
                        "error": "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                    }
                }
            }
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

    @pytest.mark.asyncio
    async def test_fetch_security_ratings_from_identifiers(
        self, httpx_client: httpx2.AsyncClient, add_security_ratings_mock_resp: None
    ) -> None:
        """
        WHEN we request security ratings (using security_id)
        THEN we get back the security's ratings.
        """

        resp = await fetch_security_ratings_from_identifiers(
            security_ids=["123456789"],
            httpx_client=httpx_client,
        )

        expected_ratings = SecurityRatings(
            ciq_security_id=123456789,
            ratings={
                "FCLONG": RatingTypeData(
                    source="S&P Global",
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
            },
        )

        assert resp.results["123456789"] == expected_ratings
        assert resp.errors == {}

    @pytest.mark.asyncio
    async def test_get_security_ratings_from_identifiers(
        self,
        httpx_client: httpx2.AsyncClient,
        httpx2_mock,
    ) -> None:
        """
        WHEN we request ratings for a security and a non-existent identifier
        THEN we get back the security's ratings and an error for the non-existent identifier.
        """
        httpx2_mock.post("https://kfinance.kensho.com/api/v1/ratings/security_ratings/").respond(
            json={
                "results": {
                    "123456789": {
                        "ciq_security_id": 123456789,
                        "ratings": {
                            "FCLONG": {
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
                                "source": "S&P Global",
                            }
                        },
                    }
                },
                "errors": {"invalid-id": "No ratings found for identifier invalid-id"},
            }
        )

        expected_ratings = SecurityRatings(
            ciq_security_id=123456789,
            ratings={
                "FCLONG": RatingTypeData(
                    source="S&P Global",
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
            },
        )

        expected_resp = GetSecurityRatingsFromIdentifiersResp(
            results={"123456789": expected_ratings},
            errors=["invalid-id: No ratings found for identifier invalid-id"],
        )

        resp = await get_security_ratings_from_identifiers(
            security_ids=["123456789", "invalid-id"],
            httpx_client=httpx_client,
        )

        assert resp == expected_resp
