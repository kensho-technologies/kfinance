from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from kfinance.client.models.date_and_period_models import EstimatePeriodType, EstimateType


class LineItem(BaseModel):
    name: str
    value: Decimal | None


class EstimatesPeriodData(BaseModel):
    period_end_date: date
    estimates: list[LineItem]


class EstimatesResp(BaseModel):
    estimate_type: EstimateType
    currency: str | None
    period_type: EstimatePeriodType
    periods: dict[str, EstimatesPeriodData]


class ConsensusTargetPriceItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias="Line Item")
    value: Decimal | None = Field(alias="Value")


class ConsensusTargetPriceResp(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    currency: str | None
    effective_date: date
    estimates: list[ConsensusTargetPriceItem]


class AnalystRecommendationsItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias="Line Item")
    value: Decimal | None = Field(alias="Value")


class AnalystRecommendationsResp(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    effective_date: date | None
    estimates: list[AnalystRecommendationsItem]
