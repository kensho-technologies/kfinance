from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, model_validator

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
    """Response from the /estimates/ endpoint for a single company.

    The API returns {"results": {company_id: ...}, "errors": {company_id: ...}}.
    The model_validator extracts the single result (if any) and collects errors.
    """

    result: Estimates | None = None
    errors: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def extract_single_result(cls, data: Any) -> Any:
        if isinstance(data, dict) and "results" in data:
            results = data.get("results", {})
            errors = data.get("errors", {})
            return {
                "result": next(iter(results.values()), None),
                "errors": list(errors.values()),
            }
        return data


class ConsensusTargetPriceItem(BaseModel):
    name: str
    value: Decimal | None


class ConsensusTargetPrice(BaseModel):
    currency: str | None
    effective_date: date
    estimates: list[ConsensusTargetPriceItem]


class ConsensusTargetPriceResp(BaseModel):
    """Response from the /estimates/consensus_target_price/ endpoint for a single company.

    The API returns {"results": {company_id: ...}, "errors": {company_id: ...}}.
    The model_validator extracts the single result (if any) and collects errors.
    """

    result: ConsensusTargetPrice | None = None
    errors: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def extract_single_result(cls, data: Any) -> Any:
        if isinstance(data, dict) and "results" in data:
            results = data.get("results", {})
            errors = data.get("errors", {})
            return {
                "result": next(iter(results.values()), None),
                "errors": list(errors.values()),
            }
        return data


class AnalystRecommendationsItem(BaseModel):
    name: str
    value: Decimal | None


class AnalystRecommendations(BaseModel):
    effective_date: date | None
    estimates: list[AnalystRecommendationsItem]


class AnalystRecommendationsResp(BaseModel):
    """Response from the /estimates/analyst_recommendations/ endpoint for a single company.

    The API returns {"results": {company_id: ...}, "errors": {company_id: ...}}.
    The model_validator extracts the single result (if any) and collects errors.
    """

    result: AnalystRecommendations | None = None
    errors: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def extract_single_result(cls, data: Any) -> Any:
        if isinstance(data, dict) and "results" in data:
            results = data.get("results", {})
            errors = data.get("errors", {})
            return {
                "result": next(iter(results.values()), None),
                "errors": list(errors.values()),
            }
        return data
