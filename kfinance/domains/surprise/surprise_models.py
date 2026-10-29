from datetime import date
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, Field, model_validator

from kfinance.client.models.date_and_period_models import EstimatePeriodType, EstimateType
from kfinance.client.models.type_aliases import Source


class Surprises(BaseModel):
    estimate_type: EstimateType | str
    period_type: EstimatePeriodType


class SurpriseLineItem(BaseModel):
    name: str
    estimate_value: Decimal | None
    actual_value: Decimal | None
    pct_changed: Decimal | None = None
    bps_changed: Decimal | None = None
    sources: list[Source] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_exclusive_or_neither(self) -> Self:
        if self.pct_changed is not None and self.bps_changed is not None:
            raise ValueError("surprise item should have pct_changed or bps_changed but not both")

        return self


class VaSurprisesPeriodData(BaseModel):
    period_end_date: date
    surprises: list[SurpriseLineItem]


class VisibleAlphaSurprises(Surprises):
    estimate_type: str
    periods: dict[str, VaSurprisesPeriodData]
