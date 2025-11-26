from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, model_validator
from strenum import StrEnum


class SegmentType(StrEnum):
    """The type of segment"""

    business = "business"
    geographic = "geographic"


class SegmentPeriodData(BaseModel):
    period_end_date: date | None = None
    num_months: int | None = None
    segments: dict[str, dict[str, Decimal | None]]  # segment_name -> line_item -> value


class SegmentsResp(BaseModel):
    currency: str | None
    periods: dict[str, SegmentPeriodData]  # period -> segment and period data

    @model_validator(mode="before")
    @classmethod
    def reshape_api_response(cls, data: Any) -> Any:
        """Transform the API response format to match the model structure.

        Pre-processed API response:
        {
            "currency": "USD",
            "segments": {
                "CY2021": {
                    "Segment Name": {"line_item": value},
                    "period_end_date": "2021-12-31",
                    "num_months": 12
                }
            }
        }

        Post-processed API response:
        {
            "currency": "USD",
            "periods": {
                "CY2021": {
                    "period_end_date": "2021-12-31",
                    "num_months": 12,
                    "segments": {
                        "Segment Name": {"line_item": value}
                    }
                }
            }
        }
        """
        if not isinstance(data, dict):
            return data

        # If we have "segments", transform it to "periods"
        if "segments" in data:
            transformed_periods = {}

            for period_key, period_data in data["segments"].items():
                if not isinstance(period_data, dict):
                    continue

                # Extract the metadata fields
                period_end_date = period_data.get("period_end_date")
                num_months = period_data.get("num_months")

                # Extract segment data (everything except the metadata fields)
                segments_data = {
                    k: v
                    for k, v in period_data.items()
                    if k not in ("period_end_date", "num_months")
                }

                transformed_period = {"segments": segments_data}

                if period_end_date is not None:
                    transformed_period["period_end_date"] = period_end_date
                if num_months is not None:
                    transformed_period["num_months"] = num_months

                transformed_periods[period_key] = transformed_period

            return {
                **data,
                "periods": transformed_periods,
                **{k: v for k, v in data.items() if k != "segments"},
            }

        return data
