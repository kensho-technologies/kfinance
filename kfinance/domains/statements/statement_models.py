from datetime import date
from decimal import Decimal

from pydantic import BaseModel
from strenum import StrEnum


class StatementType(StrEnum):
    """The type of financial statement"""

    balance_sheet = "balance_sheet"
    income_statement = "income_statement"
    cashflow = "cashflow"


class StatementPeriodData(BaseModel):
    period_end_date: date
    num_months: int
    statements: dict[str, Decimal | None]  # line_item -> value


class StatementsResp(BaseModel):
    currency: str | None
    statements: dict[str, StatementPeriodData]  # period -> statement and period data
