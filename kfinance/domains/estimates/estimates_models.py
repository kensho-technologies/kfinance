from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, model_validator

from kfinance.client.models.date_and_period_models import EstimatePeriodType, EstimateType


class LineItem(BaseModel):
    name: str
    value: Decimal | None


class EstimatesPeriodData(BaseModel):
    period_end_date: date
    estimates: list[LineItem]


class Estimates(BaseModel):
    estimate_type: EstimateType
    currency: str | None
    period_type: EstimatePeriodType
    periods: dict[str, EstimatesPeriodData]


class EstimatesResp(BaseModel):
    """Wraps a PostResponse[Estimates] for the sync client, extracting the single result."""

    result: Estimates | None = None
    errors: list[str] = []

    @model_validator(mode="before")
    @classmethod
    def from_post_response(cls, data: Any) -> Any:
        """Convert PostResponse format {results: {id: ...}, errors: {id: ...}} to single result."""
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            result = list(results.values())[0] if results else None
            errors = list(data.get("errors", {}).values())
            return {"result": result, "errors": errors}
        return data


class ConsensusTargetPriceItem(BaseModel):
    name: str
    value: Decimal | None


class ConsensusTargetPrice(BaseModel):
    currency: str | None
    effective_date: date
    estimates: list[ConsensusTargetPriceItem]


class ConsensusTargetPriceResp(BaseModel):
    """Wraps a PostResponse[ConsensusTargetPrice] for the sync client, extracting the single result."""

    result: ConsensusTargetPrice | None = None
    errors: list[str] = []

    @model_validator(mode="before")
    @classmethod
    def from_post_response(cls, data: Any) -> Any:
        """Convert PostResponse format to single result."""
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            result = list(results.values())[0] if results else None
            errors = list(data.get("errors", {}).values())
            return {"result": result, "errors": errors}
        return data


class AnalystRecommendationsItem(BaseModel):
    name: str
    value: Decimal | None


class AnalystRecommendations(BaseModel):
    effective_date: date | None
    estimates: list[AnalystRecommendationsItem]


class AnalystRecommendationsResp(BaseModel):
    """Wraps a PostResponse[AnalystRecommendations] for the sync client, extracting the single result."""

    result: AnalystRecommendations | None = None
    errors: list[str] = []

    @model_validator(mode="before")
    @classmethod
    def from_post_response(cls, data: Any) -> Any:
        """Convert PostResponse format to single result."""
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            result = list(results.values())[0] if results else None
            errors = list(data.get("errors", {}).values())
            return {"result": result, "errors": errors}
        return data
