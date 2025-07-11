from copy import deepcopy
from datetime import date
from typing import Any, TypedDict

from pydantic import BaseModel, model_validator

from kfinance.client.models.decimal_with_unit import Money, Shares


class HistoryMetadata(TypedDict):
    currency: str
    symbol: str
    exchange_name: str
    instrument_type: str
    first_trade_date: date


class Prices(BaseModel):
    """Prices represents prices for a stock for a specific "date".

    I'm putting "date" in quotes because dates can be daily ("2024-01-01"),
    weekly ("2024 Week 2"), monthly ("January 2024"), or annual ("2024").
    """

    date: str
    open: Money
    high: Money
    low: Money
    close: Money
    volume: Shares


class PriceHistory(BaseModel):
    """PriceHistory represents stock prices over a time range."""

    prices: list[Prices]

    @model_validator(mode="before")
    @classmethod
    def inject_currency_into_data(cls, data: Any) -> Any:
        """Inject the currency into each open/high/low/close price.

        The price history response only includes the currency as a top level element.
        However, the Prices model expects the unit to be included with each price.
        Before:
            {
                "date": "2024-06-25",
                "open": "445.790000",
                "high": "449.240000",
                ...
            }
        After:
            {
                "date": "2024-06-25",
                "open": {"value": "445.790000", "unit": "USD"},
                "high": {"value": "449.240000", "unit": "USD"},
                ...
            }

        Note: Volume does not need the unit injected because the Shares class
            already has "Shares" encoded. However, currencies differ between companies,
            so we need to inject that information.
        """
        if isinstance(data, dict) and "currency" in data:
            data = deepcopy(data)
            currency = data["currency"]
            for capitalization in data["prices"]:
                for key in ["open", "high", "low", "close"]:
                    capitalization[key] = dict(unit=currency, value=capitalization[key])
        return data
