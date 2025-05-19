from decimal import Decimal
from typing import Any

import pandas as pd
from pydantic import BaseModel, model_serializer, model_validator, ConfigDict, Field, AliasPath
from datetime import date

class Currency(BaseModel):
    # iso code could maybe be an enum
    iso_code: str
    num: int
    name: str
    conventional_decimals: int | None = None
    symbol: str | None = None

    model_config = ConfigDict(populate_by_name=True)

CURRENCIES = [
    Currency(iso_code="USD", num=840, conventional_decimals=2, name="United States dollar", symbol="$"),
    Currency(iso_code="EUR", num=978, conventional_decimals=2, name="Euro", symbol="\u20ac"),
    Currency(iso_code="*SH", num=1, conventional_decimals=0, name="Shares")
]
ISO_TO_CURRENCY_MAP = {c.iso_code: c for c in CURRENCIES}


class Money(BaseModel):

    value: Decimal
    currency: Currency


    model_config = ConfigDict(populate_by_name=True)

    @model_serializer
    def serialize_model(self) -> str:
        # Usual serializer would return a dict including all details on the currency.
        # Return a simple string instead.
        return f"{self.value} {self.currency.iso_code}"

    @model_validator(mode="before")
    def deserialize_model(self, value: Any):
        if isinstance(self, dict):
            return self
        # Because we have replaced the usual serializer (returning dict) with a serializer
        # that returns a string, we now need a deserializer for strings to return a
        # Money class.
        elif isinstance(self, str):
            value, iso_code = self.rsplit(sep=" ", maxsplit=1)
            return dict(value=value, currency=ISO_TO_CURRENCY_MAP[iso_code])
        else:
            raise ValueError(f"{type(self)} is not a valid input for a Money model.")

    def __add__(self, other):
        if isinstance(other, Money) and other.currency == self.currency:
            return Money(value=self.value + other.value, currency=self.currency)

    def __radd__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        if (
            isinstance(other, (int, float, Decimal))
            or isinstance(other, Money) and other.currency == self.currency
           ):
            return Money(value=self.value * other, currency=self.currency)
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __repr__(self) -> str:
        """Represents the number as an instance of Money."""
        return "Money('%s')" % str(self)

    def __str__(self) -> str:
        """Return string representation of the money"""
        return f"{self.currency.symbol if self.currency.symbol else ''}{self.value.__str__()}{'' if self.currency.symbol else ' ' + self.currency.iso_code}"


class Capitalization(BaseModel):
    """Represents one day of data in a capitalization response"""
    date: date
    market_cap: Money
    tev: Money
    shares_outstanding: Money


class Capitalizations(BaseModel):

    # a full capitalizations response consists of a list of daily capitalizations
    capitalizations: list[Capitalization] = Field(validation_alias=AliasPath("market_caps"))

    @property
    def df(self) -> pd.DataFrame:
        """Return a dataframe built from Capitalizations."""
        return pd.DataFrame({
            "market_caps": [c.market_cap for c in self.capitalizations],
            "tev": [c.tev for c in self.capitalizations],
            "shares_outstanding": [c.shares_outstanding for c in self.capitalizations],
            "dates": [c.date for c in self.capitalizations],
        })

# Sample Backend response
resp = {
    "market_caps": [
        {
            "date": "2024-01-01",
            "market_cap": "139556736000.000000 USD",
            "tev": "153629736000.000000 USD",
            "shares_outstanding": "316800000 *SH",
        },
        {
            "date": "2024-01-02",
            "market_cap": "138248352000.000000 USD",
            "tev": "152321352000.000000 USD",
            "shares_outstanding": "316800000 *SH",
        },
]
}


# build Money model
usd_from_model = Money(value=100, currency=ISO_TO_CURRENCY_MAP["USD"])

# deserialize from string
usd_from_str = Money.model_validate("10.0 USD")

# Mathematical operations
print(usd_from_str)                     # $100
print(usd_from_str * Decimal('1.5'))    # $150.0
print(Decimal('2.5') * usd_from_str)    # $250.0

# Serialize
print(usd_from_str.model_dump_json())   # "10.0 USD"


# deserialized capitalization backend response
caps = Capitalizations.model_validate(resp)

# access dataframe
df = caps.df
"""
            market_caps                   tev shares_outstanding       dates
0  $139556736000.000000  $153629736000.000000      316800000 *SH  2024-01-01
1  $138248352000.000000  $152321352000.000000      316800000 *SH  2024-01-02
"""

# mathematical operations in dataframe
print(df["market_caps"].sum())   # $277805088000.000000