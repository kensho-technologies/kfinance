from datetime import date

from pydantic import BaseModel
from strenum import StrEnum


class PeriodType(StrEnum):
    """The period type"""

    annual = "annual"
    quarterly = "quarterly"
    ltm = "ltm"
    ytd = "ytd"


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
