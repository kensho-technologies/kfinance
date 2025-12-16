from datetime import date
from decimal import Decimal
from typing import TypeAlias

from pydantic import BaseModel, Field


Source: TypeAlias = dict[str, str]


class LineItem(BaseModel):
    name: str
    value: Decimal | None
    sources: list[Source] = Field(default_factory=list)


class EstimatesPeriodData(BaseModel):
    period_end_date: date
    num_months: int
    estimates: LineItem


class EstimatesResp(BaseModel):
    currency: str | None
    periods: dict[str, EstimatesPeriodData]
