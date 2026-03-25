from datetime import date
from decimal import Decimal
import logging
from typing import Any, Callable, Dict

from pydantic import BaseModel, model_serializer, model_validator

from kfinance.client.models.date_and_period_models import EstimatePeriodType, EstimateType


logger = logging.getLogger(__name__)


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
    """Response model for a single company's estimates."""

    result: Estimates | None = None
    error: str | None = None

    @model_serializer(mode="wrap")
    def serialize_model(self, handler: Callable) -> Dict[str, Any]:
        """Make `error` the last response field and only include if there is at least one error."""
        data = handler(self)
        error = data.pop("error")
        if error:
            data["error"] = error
        return data

    @model_validator(mode="before")
    @classmethod
    def from_post_response(cls, data: Any) -> Any:
        """Extract the single result from the API response."""
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            if len(results) > 1:
                logger.warning("Expected at most one result, got %d", len(results))
            result = next(iter(results.values()), None)
            errors = data.get("errors", {})
            if len(errors) > 1:
                logger.warning("Expected at most one error, got %d", len(errors))
            error = next(iter(errors.values()), None)
            return {"result": result, "error": error}
        return data


class ConsensusTargetPriceItem(BaseModel):
    name: str
    value: Decimal | None


class ConsensusTargetPrice(BaseModel):
    currency: str | None
    effective_date: date
    estimates: list[ConsensusTargetPriceItem]


class ConsensusTargetPriceResp(BaseModel):
    """Response model for a single company's consensus target price."""

    result: ConsensusTargetPrice | None = None
    error: str | None = None

    @model_serializer(mode="wrap")
    def serialize_model(self, handler: Callable) -> Dict[str, Any]:
        """Make `error` the last response field and only include if there is at least one error."""
        data = handler(self)
        error = data.pop("error")
        if error:
            data["error"] = error
        return data

    @model_validator(mode="before")
    @classmethod
    def from_post_response(cls, data: Any) -> Any:
        """Extract the single result from the API response."""
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            if len(results) > 1:
                logger.warning("Expected at most one result, got %d", len(results))
            result = next(iter(results.values()), None)
            errors = data.get("errors", {})
            if len(errors) > 1:
                logger.warning("Expected at most one error, got %d", len(errors))
            error = next(iter(errors.values()), None)
            return {"result": result, "error": error}
        return data


class AnalystRecommendationsItem(BaseModel):
    name: str
    value: Decimal | None


class AnalystRecommendations(BaseModel):
    effective_date: date | None
    estimates: list[AnalystRecommendationsItem]


class AnalystRecommendationsResp(BaseModel):
    """Response model for a single company's analyst recommendations."""

    result: AnalystRecommendations | None = None
    error: str | None = None

    @model_serializer(mode="wrap")
    def serialize_model(self, handler: Callable) -> Dict[str, Any]:
        """Make `error` the last response field and only include if there is at least one error."""
        data = handler(self)
        error = data.pop("error")
        if error:
            data["error"] = error
        return data

    @model_validator(mode="before")
    @classmethod
    def from_post_response(cls, data: Any) -> Any:
        """Extract the single result from the API response."""
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            if len(results) > 1:
                logger.warning("Expected at most one result, got %d", len(results))
            result = next(iter(results.values()), None)
            errors = data.get("errors", {})
            if len(errors) > 1:
                logger.warning("Expected at most one error, got %d", len(errors))
            error = next(iter(errors.values()), None)
            return {"result": result, "error": error}
        return data
