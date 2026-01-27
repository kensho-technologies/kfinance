from datetime import date
from decimal import Decimal
from typing import TypeAlias

from pydantic import BaseModel, Field

from kfinance.client.models.date_and_period_models import EstimateType, EstimatePeriodType

Source: TypeAlias = dict[str, str]


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
