from copy import deepcopy
from datetime import date
from typing import Any

from pydantic import BaseModel, Field, model_validator
from strenum import StrEnum

from kfinance.client.models.decimal_with_unit import Money, Shares


class Capitalization(StrEnum):
    """The capitalization type"""

    market_cap = "market_cap"
    tev = "tev"
    shares_outstanding = "shares_outstanding"


class DailyCapitalization(BaseModel):
    """DailyCapitalization represents market cap, TEV, and shares outstanding for a day"""

    date: date
    market_cap: Money
    tev: Money
    shares_outstanding: Shares


class Capitalizations(BaseModel):
    """Capitalizations represents market cap, TEV, and shares outstanding for a date range"""

    capitalizations: list[DailyCapitalization] = Field(validation_alias="market_caps")

    @model_validator(mode="before")
    @classmethod
    def inject_currency_into_data(cls, data: Any) -> Any:
        """Inject the currency into each market_cap and TEV.

        The capitalization response only includes the currency as a top level element.
        However, the capitalizations model expects the unit to be included with each market cap
        and tev.
        Before:
            "market_caps": [
                {
                    "date": "2024-06-24",
                    "market_cap": "139231113000.000000",
                    "tev": "153942113000.000000",
                    "shares_outstanding": 312900000
                },
            ]
        After:
            "market_caps": [
                {
                    "date": "2024-06-24",
                    "market_cap": {"value": "139231113000.000000", "unit": "USD"},
                    "tev": {"value": "153942113000.000000", "unit": "USD"},
                    "shares_outstanding": 312900000
                },

        Note: shares_outstanding does not need the unit injected because the Shares class
            already has "Shares" encoded. However, currencies differ between companies,
            so we need to inject that information.
        """
        if isinstance(data, dict) and "currency" in data:
            data = deepcopy(data)
            currency = data["currency"]
            for capitalization in data["market_caps"]:
                for key in ["market_cap", "tev"]:
                    capitalization[key] = dict(unit=currency, value=capitalization[key])
        return data

    def model_dump_json_single_metric(
        self, capitalization_metric: Capitalization, only_include_most_recent_value: bool = False
    ) -> dict:
        """Dump only a single metric (market cap, tev, or shares outstanding) to json

        If only_include_most_recent_value is set to True, only the most recent value gets included.

        Sample response:
        [
            {
                'date': datetime.date(2024, 4, 10),
                'market_cap': {'value': Decimal('132766738270.00'), 'unit': 'USD'}
            }
        ]
        """

        return self.model_dump(
            mode="json",
            include={  # type: ignore[arg-type]
                "capitalizations": {
                    0 if only_include_most_recent_value else "__all__": {
                        "date",
                        capitalization_metric.value,
                    }
                }
            },
        )["capitalizations"]
