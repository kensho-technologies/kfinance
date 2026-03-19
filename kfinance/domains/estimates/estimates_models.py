import logging
from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, model_validator

from kfinance.client.models.date_and_period_models import EstimatePeriodType, EstimateType
from kfinance.client.models.response_models import RespWithErrors

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


class EstimatesResp(RespWithErrors):
    """Response model for a single company's estimates."""

    result: Estimates | None = None

    @model_validator(mode="before")
    @classmethod
    def from_post_response(cls, data: Any) -> Any:
        """Extract the single result from the API response.

        Can be populated in two ways:
        1. From the API response format (via model_validate):
            {"results": {"12345": {...}}, "errors": {}}
            -> {"result": {...}, "errors": {}}
        2. Directly (e.g. in tests):
            {"result": Estimates(...), "errors": {}}
        """
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            if len(results) > 1:
                logger.warning("Expected at most one result, got %d", len(results))
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
        """Extract the single result from the API response.

        Can be populated in two ways:
        1. From the API response format (via model_validate):
            {"results": {"12345": {...}}, "errors": {}}
            -> {"result": {...}, "errors": {}}
        2. Directly (e.g. in tests):
            {"result": ConsensusTargetPrice(...), "errors": {}}
        """
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            if len(results) > 1:
                logger.warning("Expected at most one result, got %d", len(results))
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
        """Extract the single result from the API response.

        Can be populated in two ways:
        1. From the API response format (via model_validate):
            {"results": {"12345": {...}}, "errors": {}}
            -> {"result": {...}, "errors": {}}
        2. Directly (e.g. in tests):
            {"result": AnalystRecommendations(...), "errors": {}}
        """
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            if len(results) > 1:
                logger.warning("Expected at most one result, got %d", len(results))
            result = next(iter(results.values()), None)
            return {"result": result, "errors": data.get("errors", {})}
        return data
