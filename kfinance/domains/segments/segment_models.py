from typing import Any, Optional
from datetime import date
from decimal import Decimal

from pydantic import BaseModel
from strenum import StrEnum

from kfinance.client.models.date_and_period_models import CalendarType


class SegmentType(StrEnum):
    """The type of segment"""

    business = "business"
    geographic = "geographic"


class SegmentsResp(BaseModel):
    segments: dict[str, Any]


class SegmentPeriodData(BaseModel):
    """Enhanced segment data with period metadata"""
    period_end_date: date
    num_months: int
    segments: dict[str, dict[str, Optional[Decimal]]]  # segment_name -> line_item -> value


class SegmentsCurrencyResponse(BaseModel):
    """Response for segments data including currency and enhanced period metadata"""
    currency: Optional[str]
    segments: dict[str, SegmentPeriodData]  # period -> segment data


class MultiCompanySegmentsResponse(BaseModel):
    """Response for multiple companies segments requests"""
    results: dict[str, SegmentsCurrencyResponse]  # company_id -> response
    errors: dict[str, str]  # company_id -> error_message


