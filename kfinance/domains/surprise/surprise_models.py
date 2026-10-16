from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from kfinance.client.models.date_and_period_models import EstimatePeriodType, EstimateType
from kfinance.client.models.type_aliases import Source


class Surprises(BaseModel):
    estimate_type: EstimateType | str
    period_type: EstimatePeriodType


class SurpriseLineItem(BaseModel):
    name: str
    estimate_value: Decimal | None
    actual_value: Decimal | None
    pct_changed: Decimal | None
    sources: list[Source] = Field(default_factory=list)


class VaSurprisesPeriodData(BaseModel):
    period_end_date: date
    surprises: list[SurpriseLineItem]


class VisibleAlphaSurprises(Surprises):
    estimate_type: str
    periods: dict[str, VaSurprisesPeriodData]
