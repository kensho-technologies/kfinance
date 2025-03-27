from typing import Literal

from pydantic import BaseModel, Field

from .constants import LINE_ITEM_NAMES_AND_ALIASES, BusinessRelationshipType


class GetLatestInput(BaseModel):
    use_local_timezone: bool = Field(
        default=True, description="whether to use the local timezone of the user"
    )


class GetNQuartersAgoInput(BaseModel):
    n: int = Field(description="number of quarters before the current quarter")


class GetCompanyIdFromIdentifier(BaseModel):
    ticker_str: str = Field(description="The ticker")


class GetSecurityIdFromIdentifier(BaseModel):
    identifier: str = Field(
        description="The identifier, which can be a ticker symbol, ISIN, or CUSIP"
    )


class GetTradingItemIdFromIdentifier(BaseModel):
    identifier: str = Field(
        description="The identifier, which can be a ticker symbol, ISIN, or CUSIP"
    )


class GetIsinFromTicker(BaseModel):
    ticker_str: str = Field(description="The ticker")


class GetCusipFromTicker(BaseModel):
    ticker_str: str = Field(description="The ticker")


class GetInfoFromIdentifier(BaseModel):
    identifier: str = Field(
        description="The identifier, which can be a ticker symbol, ISIN, or CUSIP"
    )


class GetEarningsCallDatetimesFromIdentifier(BaseModel):
    identifier: str = Field(
        description="The identifier, which can be a ticker symbol, ISIN, or CUSIP"
    )


class GetHistoryMetadataFromIdentifier(BaseModel):
    identifier: str = Field(
        description="The identifier, which can be a ticker symbol, ISIN, or CUSIP"
    )


class GetPricesFromIdentifier(BaseModel):
    identifier: str = Field(
        description="The identifier, which can be a ticker symbol, ISIN, or CUSIP"
    )
    periodicity: Literal["day", "week", "month", "year"] = Field(
        default="day",
        description="The frequency or interval at which the historical data points are sampled or aggregated. Periodicity is not the same as the date range. The date range specifies the time span over which the data is retrieved, while periodicity determines how the data within that date range is aggregated, valid inputs are ['day', 'week', 'month', 'year'].",
    )
    adjusted: bool = Field(
        description="Whether to retrieve adjusted prices that account for corporate actions such as dividends and splits."
    )
    start_date: str | None = Field(
        default=None,
        description="The start date for historical price retrieval in format YYYY-MM-DD",
    )
    end_date: str | None = Field(
        default=None, description="The end date for historical price retrieval in format YYYY-MM-DD"
    )


class GetCapitalizationFromIdentifier(BaseModel):
    identifier: str = Field(
        description="The identifier, which can be a ticker symbol, ISIN, or CUSIP"
    )
    capitalization: Literal["market_cap", "tev", "shares_outstanding"] = Field(
        description="The capitalization to retrieve"
    )
    start_date: str | None = Field(
        default=None,
        description="The start date in format YYYY-MM-DD",
    )
    end_date: str | None = Field(default=None, description="The end date in format YYYY-MM-DD")


class GetFinancialStatementFromIdentifier(BaseModel):
    identifier: str = Field(
        description="The identifier, which can be a ticker symbol, ISIN, or CUSIP"
    )
    statement: Literal["balance_sheet", "income_statement", "cashflow"] = Field(
        description="The type of financial statement, valid inputs are ['balance_sheet', 'income_statement', 'cashflow']"
    )
    period_type: Literal["annual", "quarterly", "ltm", "ytd"] | None = Field(
        default=None,
        description="time period type, valid inputs are ['annual', 'quarterly', 'ltm', 'ytd'].",
    )
    start_year: int | None = Field(
        default=None, description="The starting year for the data range."
    )
    end_year: int | None = Field(default=None, description="The ending year for the data range.")
    start_quarter: Literal[1, 2, 3, 4] | None = Field(
        default=None, description="starting quarter, valid inputs are [1, 2, 3, 4]"
    )
    end_quarter: Literal[1, 2, 3, 4] | None = Field(
        default=None, description="ending quarter, valid inputs are [1, 2, 3, 4]"
    )


class GetFinancialLineItemFromIdentifier(BaseModel):
    identifier: str = Field(
        description="The identifier, which can be a ticker symbol, ISIN, or CUSIP"
    )
    line_item: Literal[tuple(LINE_ITEM_NAMES_AND_ALIASES)] = Field(  # type: ignore
        description="The type of financial line_item requested"
    )
    period_type: Literal["annual", "quarterly", "ltm", "ytd"] | None = Field(
        default=None,
        description="time period type, valid inputs are ['annual', 'quarterly', 'ltm', 'ytd']",
    )
    start_year: int | None = Field(
        default=None, description="The starting year for the data range."
    )
    end_year: int | None = Field(default=None, description="The ending year for the data range.")
    start_quarter: Literal[1, 2, 3, 4] | None = Field(
        default=None, description="starting quarter, valid inputs are [1, 2, 3, 4]"
    )
    end_quarter: Literal[1, 2, 3, 4] | None = Field(
        default=None, description="ending quarter, valid inputs are [1, 2, 3, 4]"
    )


class GetBusinessRelationshipFromIdentifier(BaseModel):
    identifier: str = Field(
        description="The identifier, which can be a ticker symbol, ISIN, or CUSIP"
    )
    business_relationship: BusinessRelationshipType = Field(
        description="The type of business relationship requested"
    )
