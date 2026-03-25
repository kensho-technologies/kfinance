from datetime import date

from pydantic import BaseModel
from strenum import StrEnum

from kfinance.domains.line_items.line_item_models import BasePeriodsResp, LineItem


class StatementType(StrEnum):
    """The type of financial statement"""

    balance_sheet = "balance_sheet"
    income_statement = "income_statement"
    cashflow = "cashflow"


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
