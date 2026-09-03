from datetime import date
from typing import Any

from pydantic import BaseModel
from strenum import StrEnum

from kfinance.domains.line_items.line_item_models import BasePeriodsResp, LineItem


class StatementType(StrEnum):
    """The type of financial statement"""

    balance_sheet = "balance_sheet"
    income_statement = "income_statement"
    cashflow = "cashflow"


def normalize_statement_type(v: Any) -> Any:
    """Normalize 'cash_flow' to 'cashflow' before enum validation.

    LLMs infer 'cash_flow' from the underscore pattern of the other enum values
    (balance_sheet, income_statement).
    """
    if isinstance(v, str) and v == "cash_flow":
        return "cashflow"
    return v


class Statement(BaseModel):
    name: str
    line_items: list[LineItem]


class StatementPeriodData(BaseModel):
    period_end_date: date
    num_months: int
    statements: list[Statement]


class StatementsResp(BasePeriodsResp):
    currency: str | None
    periods: dict[str, StatementPeriodData]  # period -> statement and period data
