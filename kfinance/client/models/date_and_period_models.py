from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field
from strenum import StrEnum


NumPeriodsForward = Annotated[
    int,
    Field(ge=0, le=99, description="The number of periods in the future to retrieve estimate data."),
]


NumPeriodsBackward = Annotated[
    int,
    Field(ge=0, le=99, description="The number of periods in the past to retrieve estimate data.",),
]


class PeriodType(StrEnum):
    """The period type"""

    annual = "annual"
    quarterly = "quarterly"
    ltm = "ltm"
    ytd = "ytd"


class EstimatePeriodType(StrEnum):
    annual = "annual"
    quarterly = "quarterly"
    fiscal_half = "fiscal_half"


class EstimateType(StrEnum):
    estimate = "estimate"
    guidance = "guidance"


class Periodicity(StrEnum):
    """The frequency or interval at which the historical data points are sampled or aggregated. Periodicity is not the same as the date range. The date range specifies the time span over which the data is retrieved, while periodicity determines how the data within that date range is aggregated."""

    day = "day"
    week = "week"
    month = "month"
    year = "year"


class YearAndQuarter(BaseModel):
    year: int
    quarter: int


class LatestAnnualPeriod(BaseModel):
    latest_year: int


class LatestQuarterlyPeriod(BaseModel):
    latest_quarter: int
    latest_year: int


class CurrentPeriod(BaseModel):
    current_year: int
    current_quarter: int
    current_month: int
    current_date: date


class LatestPeriods(BaseModel):
    annual: LatestAnnualPeriod
    quarterly: LatestQuarterlyPeriod
    now: CurrentPeriod
