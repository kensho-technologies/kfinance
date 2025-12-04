from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel
from strenum import StrEnum


class StatementType(StrEnum):
    """The type of financial statement"""

    balance_sheet = "balance_sheet"
    income_statement = "income_statement"
    cashflow = "cashflow"


class LineItem(BaseModel):
    name: str
    value: Decimal | None
    sources: list[dict[str, Any]] | None = None


class Statement(BaseModel):
    name: str
    line_items: list[LineItem]


class StatementPeriodData(BaseModel):
    period_end_date: date
    num_months: int
    statements: list[Statement]


class StatementsResp(BaseModel):
    currency: str | None
    periods: dict[str, StatementPeriodData]  # period -> statement and period data
