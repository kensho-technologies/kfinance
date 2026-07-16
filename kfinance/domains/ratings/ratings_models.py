from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class EntityInfo(BaseModel):
    """Resolved entity information for a single identifier.

    An entity represents any rateable entity in the ratings system, including sovereigns.
    The user will provide an identifier (e.g., "AAPL", "USA", "Microsoft")
    which gets resolved to an entity_id.

    Note that for companies: entity_id == company_id and
    for sovereigns/countries: entity_id is a unique ID for that country.
    """

    entity_id: int
    entity_name: str | None
    ticker: str | None
    country: str | None


class EntityIdResp(BaseModel):
    """A response from the resolve_entities endpoint (POST /ratings/resolve_entities).

    For easier handling within tools, we split the api response into
    identifiers_resolved (successful resolution) and errors (resolution failed).
    """

    identifiers_resolved: dict[str, EntityInfo] = Field(
        description="A mapping of all identifiers that could successfully be resolved"
        "to the corresponding identification triples."
    )
    errors: dict[str, str] = Field(
        description="A mapping of all identifiers that could not be resolved."
    )

    @model_validator(mode="before")
    @classmethod
    def separate_successful_and_failed_resolutions(cls, data: Any) -> Any:
        """Split response into identifiers_resolved (success) and errors

        Pre-processed API response:
        {
            'data': {
                'USA': {'entity_id': 12425677, 'entity_name': 'United States', 'ticker': null, 'country': 'USA'},
                'non-existent': {'error': 'No identification triple found for the provided identifier: NON-EXISTENT of type: ticker'}
            }
        }

        Post-processed API response:
        {
            'identifiers_resolved': {
                'USA': {'entity_id': 12425677, 'entity_name': 'United States', 'ticker': null, 'country': 'USA'},
            },
            'errors': {
                'non-existent': 'No identification triple found for the provided identifier: NON-EXISTENT of type: ticker'
            }
        }


        """
        # Separate successful and failed resolutions for kfinance api responses
        if isinstance(data, dict) and "data" in data:
            output: dict[str, dict] = dict(identifiers_resolved=dict(), errors=dict())

            for key, val in data["data"].items():
                if "error" in val:
                    output["errors"][key] = val["error"]
                else:
                    output["identifiers_resolved"][key] = val
            return output
        # In all other cases (e.g. EntityIdResp directly initialized),
        # just return the data.
        else:
            return data


class EntityInfoWithResult(BaseModel):
    """Entity information combined with issuer ratings data.

    Uses entity_name instead of company_name since entities can represent
    non-company entities (countries, sovereigns, etc.).
    """

    entity_name: str | None
    ticker: str | None
    country: str | None
    data: "IssuerRatings"


class RatingDetail(BaseModel):
    """Single rating detail (reusable for latest and history)."""

    rating: str | None = Field(default=None)
    rating_datetime: datetime
    rating_action_word: str | None = Field(default=None)
    credit_watch: str | None = Field(default=None)
    credit_watch_datetime: datetime | None = Field(default=None)
    outlook: str | None = Field(default=None)
    outlook_datetime: datetime | None = Field(default=None)


class RatingTypeData(BaseModel):
    """Data for a single rating type (e.g., FCLONG, STDSHORT)."""

    last_review_date: datetime | None = Field(default=None)
    latest: RatingDetail
    history: list[RatingDetail] = Field(default_factory=list)


class IssuerRatings(BaseModel):
    """Response structure for a single entity's issuer-level ratings.

    Nested dict structure: org_debt_type_code -> rating_type_code -> RatingTypeData
    """

    ratings: dict[str, dict[str, RatingTypeData]] = Field(default_factory=dict)


class IssuerRatingsResp(BaseModel):
    """Response structure for issuer-level ratings."""

    results: dict[str, IssuerRatings] = Field(default_factory=dict)
    errors: dict[str, str] = Field(default_factory=dict)
