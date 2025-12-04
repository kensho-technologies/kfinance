from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel
from strenum import StrEnum


class SegmentType(StrEnum):
    """The type of segment"""

    business = "business"
    geographic = "geographic"


class LineItem(BaseModel):
    name: str
    value: Decimal | None
    sources: list[dict[str, Any]] | None = None


class Segment(BaseModel):
    name: str
    line_items: list[LineItem]


class SegmentPeriodData(BaseModel):
    period_end_date: date
    num_months: int
    segments: list[Segment]


class SegmentsResp(BaseModel):
    currency: str | None
    periods: dict[str, SegmentPeriodData]  # period -> segment and period data
