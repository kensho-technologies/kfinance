from typing import TypedDict

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


class YearAndQuarter(TypedDict):
    year: int
    quarter: int


class LatestAnnualPeriod(TypedDict):
    latest_year: int


class LatestQuarterlyPeriod(TypedDict):
    latest_quarter: int
    latest_year: int


class CurrentPeriod(TypedDict):
    current_year: int
    current_quarter: int
    current_month: int
    current_date: str


class LatestPeriods(TypedDict):
    annual: LatestAnnualPeriod
    quarterly: LatestQuarterlyPeriod
    now: CurrentPeriod
