from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, model_validator

from kfinance.client.models.date_and_period_models import EstimatePeriodType, EstimateType
from kfinance.client.models.response_models import RespWithErrors


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


class EstimatesResp(RespWithErrors):
    """Response model for a single company's estimates."""

    result: Estimates | None = None

    @model_validator(mode="before")
    @classmethod
    def from_post_response(cls, data: Any) -> Any:
        """Convert PostResponse format {results: {id: ...}, errors: {id: ...}} to single result."""
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            result = next(iter(results.values()), None)
            return {"result": result, "errors": data.get("errors", {})}
        return data


class ConsensusTargetPriceItem(BaseModel):
    name: str
    value: Decimal | None


class ConsensusTargetPrice(BaseModel):
    currency: str | None
    effective_date: date
    estimates: list[ConsensusTargetPriceItem]


class ConsensusTargetPriceResp(RespWithErrors):
    """Response model for a single company's consensus target price."""

    result: ConsensusTargetPrice | None = None

    @model_validator(mode="before")
    @classmethod
    def from_post_response(cls, data: Any) -> Any:
        """Convert PostResponse format to single result."""
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            result = next(iter(results.values()), None)
            return {"result": result, "errors": data.get("errors", {})}
        return data


class AnalystRecommendationsItem(BaseModel):
    name: str
    value: Decimal | None


class AnalystRecommendations(BaseModel):
    effective_date: date | None
    estimates: list[AnalystRecommendationsItem]


class AnalystRecommendationsResp(RespWithErrors):
    """Response model for a single company's analyst recommendations."""

    result: AnalystRecommendations | None = None

    @model_validator(mode="before")
    @classmethod
    def from_post_response(cls, data: Any) -> Any:
        """Convert PostResponse format to single result."""
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            result = next(iter(results.values()), None)
            return {"result": result, "errors": data.get("errors", {})}
        return data
