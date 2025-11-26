from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, model_validator
from strenum import StrEnum


class StatementType(StrEnum):
    """The type of financial statement"""

    balance_sheet = "balance_sheet"
    income_statement = "income_statement"
    cashflow = "cashflow"


class StatementPeriodData(BaseModel):
    period_end_date: date | None = None
    num_months: int | None = None
    statements: dict[str, Decimal | None]  # line_item -> value


class StatementsResp(BaseModel):
    currency: str | None
    periods: dict[str, StatementPeriodData]  # period -> statement and period data

    @model_validator(mode="before")
    @classmethod
    def reshape_api_response(cls, data: Any) -> Any:
        """Transform the API response format to match the model structure.

        Pre-processed API response:
        {
            "currency": "USD",
            "statements": {
                "CY2020": {
                    "Revenues": "7442000000.000000",
                    "Total Revenues": "7442000000.000000",
                    "period_end_date": "2020-12-31",
                    "num_months": 12
                }
            }
        }

        Post-processed API response:
        {
            "currency": "USD",
            "statements": {
                "CY2020": {
                    "period_end_date": "2020-12-31",
                    "num_months": 12,
                    "statements": {
                        "Revenues": "7442000000.000000",
                        "Total Revenues": "7442000000.000000"
                    }
                }
            }
        }
        """
        if not isinstance(data, dict):
            return data

        # If we have "statements", transform it to "periods"
        if "statements" in data:
            transformed_statements = {}

            for period_key, period_data in data["statements"].items():
                if not isinstance(period_data, dict):
                    continue

                # Extract the metadata fields
                period_end_date = period_data.get("period_end_date")
                num_months = period_data.get("num_months")

                # Extract statement data (everything except the metadata fields)
                statements_data = {
                    k: v
                    for k, v in period_data.items()
                    if k not in ("period_end_date", "num_months")
                }

                transformed_period = {"statements": statements_data}

                if period_end_date is not None:
                    transformed_period["period_end_date"] = period_end_date
                if num_months is not None:
                    transformed_period["num_months"] = num_months

                transformed_statements[period_key] = transformed_period

            return {
                **{k: v for k, v in data.items() if k != "statements"},
                "periods": transformed_statements,
            }

        # If neither "periods" nor "statements" exist, add empty periods
        if "periods" not in data:
            return {**data, "periods": {}}

        return data
