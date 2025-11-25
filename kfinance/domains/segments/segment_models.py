from datetime import date
from decimal import Decimal

from pydantic import BaseModel
from strenum import StrEnum


class SegmentType(StrEnum):
    """The type of segment"""

    business = "business"
    geographic = "geographic"


class SegmentPeriodData(BaseModel):
    period_end_date: date
    num_months: int
    segments: dict[str, dict[str, Decimal | None]]  # segment_name -> line_item -> value


class SegmentsResp(BaseModel):
    currency: str | None
    segments: dict[str, SegmentPeriodData]  # period -> segment and period data


class MultiCompanySegmentsResp(BaseModel):
    """Response for multiple companies segments requests"""

    results: dict[str, SegmentsResp]  # company_id -> response
    errors: dict[str, str]  # company_id -> error_message
