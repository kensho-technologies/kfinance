from copy import deepcopy
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self

from kfinance.client.models.currency_models import ISO_CODE_TO_CURRENCY


class DecimalWithUnit(BaseModel):
    """DecimalWithUnit (DWU) represents a decimal with a corresponding unit like $100 or 20 shares.

    In addition to a value and unit, each DWU has a `conventional_decimals` attribute,
    which indicates the number of decimals that should be represented.
    For example, for USD, conventional_decimals is 2, which will display as "1.00".
    For shares, conventional_decimals is 0, which will display as "1"

    Usually, rather than initializing a DWU directly, you'll likely want to use an
    existing subclass like `Money` or `Shares` or create a new one.
    """

    value: Decimal = Field(allow_inf_nan=True)
    unit: str
    # exclude conventional_decimals from serialization
    conventional_decimals: int = Field(exclude=True)

    @field_validator("value", mode="before")
    @classmethod
    def convert_none_to_nan(cls, v: Any) -> Any:
        """Convert None values to NaN.

        Price data can include None for open prices.
        https://kfinance.kensho.com/api/v1/pricing/37284793/2003-01-01/2024-12-31/month/adjusted
        """
        if v is None:
            return Decimal("NaN")
        return v

    @model_validator(mode="after")
    def quantize_value(self) -> Self:
        """Quantize the value at the end of the deserialization.

        The value gets adjusted so that it always has the expected number of decimals defined in
        conventional_decimals.
        For USD with conventional_decimals=2, it will show values like "1.00"
        For Shares with conventional_decimals=0, it will show values like "1"
        """
        exponent = Decimal("10") ** Decimal(-self.conventional_decimals)
        self.value = self.value.quantize(exp=exponent)
        return self


class Money(DecimalWithUnit):
    @model_validator(mode="before")
    @classmethod
    def inject_conventional_decimals_into_data(cls, data: Any) -> Any:
        """Inject conventional_decimals into data dict.

        Each currency has an associated conventional_decimals defined in the
        CURRENCIES list. This validator fetches that number and injects it into the
        data dict.
        """

        if isinstance(data, dict) and "conventional_decimals" not in data:
            data = deepcopy(data)
            currency = ISO_CODE_TO_CURRENCY[data["unit"]]
            data["conventional_decimals"] = currency.conventional_decimals

        return data


class Shares(DecimalWithUnit):
    unit: str = "Shares"
    conventional_decimals: int = Field(exclude=True, default=0)

    @model_validator(mode="before")
    @classmethod
    def convert_numbers_to_dicts(cls, data: Any) -> Any:
        """Convert numbers into dicts.

        The shares class can be built from a single number because unit and
        conventional_decimals are always the same. However, the parser expects a
        dict instead of a number, so we have to convert any number ("10") into a
        dict {"value": "10"}.
        """

        if isinstance(data, (str, int, float, Decimal)):
            data = {"value": data}
        return data
