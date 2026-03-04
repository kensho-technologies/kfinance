from datetime import date

from pydantic import BaseModel
from strenum import StrEnum

from kfinance.domains.line_items.line_item_models import BasePeriodsResp, LineItem


class SegmentType(StrEnum):
    """The type of segment"""

    business = "business"
    geographic = "geographic"


class Segment(BaseModel):
    name: str
    line_items: list[LineItem]


class SegmentPeriodData(BaseModel):
    period_end_date: date
    num_months: int
    segments: list[Segment]


class SegmentsResp(BasePeriodsResp):
    currency: str | None
    periods: dict[str, SegmentPeriodData]  # period -> segment and period data


class SegmentsBatchResp(BaseModel):
    """Response model for batch segments API call."""

    results: dict[str, SegmentsResp]  # company_id -> segments response
    errors: dict[str, str]  # company_id -> error message
