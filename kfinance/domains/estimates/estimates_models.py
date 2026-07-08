from datetime import date
from decimal import Decimal
import logging
from typing import Any

from pydantic import BaseModel, model_validator

from kfinance.client.models.date_and_period_models import EstimatePeriodType, EstimateType


logger = logging.getLogger(__name__)


class LineItem(BaseModel):
    name: str
    value: Decimal | None


class TickerEstimatesGroup(BaseModel):
    currency: str | None
    estimates: list[LineItem]


class CiqEstimatesPeriodData(BaseModel):
    period_end_date: date
    estimates: dict[str, TickerEstimatesGroup]

    @model_validator(mode="before")
    @classmethod
    def group_by_ticker(cls, data: Any) -> Any:
        """Group a flat list of estimates by ticker_or_company.

        The API returns estimates as a flat list with ticker_or_company and currency on each item.
        This validator groups them into a dict keyed by ticker_or_company.
        For example:
        Before:
        "FY2026": {
            "period_end_date": "2026-12-31",
            "estimates": [
                {
                    "name": "EPS Consensus High",
                    "value": "14.0",
                    "currency": "EUR",
                    "ticker_or_company": "Company Level"
                },
                {
                    "name": "Book Value / Share Consensus High",
                    "value": "114.5",
                    "currency": "USD",
                    "ticker_or_company": "ENXTAM: ASM",
                }
            ]
        }

        After:
        "FY2026": {
            "period_end_date": "2026-12-31",
            "estimates": {
            "Company Level": {
                "currency": "EUR",
                "estimates": [{"name": "EPS Consensus High", "value": "14.0"}]
            },
            "ENXTAM: ASM": {
                "currency": "USD",
                "estimates": [{"name": "Book Value / Share Consensus High", "value": "114.5"}]
            }
        }
        """
        if not isinstance(data, dict):
            return data
        raw_estimates = data.get("estimates")
        if not isinstance(raw_estimates, list):
            return data
        grouped: dict[str, dict[str, Any]] = {}
        for item in raw_estimates:
            if not isinstance(item, dict):
                return data
            ticker = item.get("ticker_or_company", "Company Level")
            if ticker not in grouped:
                grouped[ticker] = {"currency": item.get("currency"), "estimates": []}
            grouped[ticker]["estimates"].append({"name": item["name"], "value": item.get("value")})
        data = {**data, "estimates": grouped}
        return data


class VaEstimatesPeriodData(BaseModel):
    period_end_date: date
    estimates: list[LineItem]


class Estimates(BaseModel):
    estimate_type: EstimateType | str
    period_type: EstimatePeriodType


class CiqEstimates(Estimates):
    estimate_type: EstimateType
    periods: dict[str, CiqEstimatesPeriodData]


class VisibleAlphaEstimates(Estimates):
    estimate_type: str
    currency: str | None
    periods: dict[str, VaEstimatesPeriodData]


class ConsensusTargetPriceItem(BaseModel):
    name: str
    value: Decimal | None


class ConsensusTargetPrice(BaseModel):
    currency: str | None
    effective_date: date
    estimates: list[ConsensusTargetPriceItem]


class AnalystRecommendationsItem(BaseModel):
    name: str
    value: Decimal | None


class AnalystRecommendations(BaseModel):
    effective_date: date | None
    estimates: list[AnalystRecommendationsItem]
