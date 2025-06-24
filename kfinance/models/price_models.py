from copy import deepcopy
from typing import Any

from pydantic import BaseModel, model_validator

from kfinance.decimal_with_unit import Money, Shares


class Prices(BaseModel):
    """Prices represents prices for a stock for a specific "date".

    I'm putting "date" in quotes because dates can be daily, weekly,
    monthly, or annual.
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
