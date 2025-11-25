from typing import Any, Optional
from datetime import date
from decimal import Decimal

from pydantic import BaseModel
from strenum import StrEnum

from kfinance.client.models.date_and_period_models import CalendarType


class StatementType(StrEnum):
    """The type of financial statement"""

    balance_sheet = "balance_sheet"
    income_statement = "income_statement"
    cashflow = "cashflow"


class StatementsResp(BaseModel):
    statements: dict[str, Any]


class StatementPeriodData(BaseModel):
    """Enhanced statement data with period metadata"""
    period_end_date: date
    num_months: int
    statements: dict[str, Optional[Decimal]]  # line_item -> value


class StatementsCurrencyResponse(BaseModel):
    """Response for statements data including currency and enhanced period metadata"""
    currency: Optional[str]
    statements: dict[str, StatementPeriodData]  # period -> statement data


class MultiCompanyStatementsResponse(BaseModel):
    """Response for multiple companies statements requests"""
    results: dict[str, StatementsCurrencyResponse]  # company_id -> response
    errors: dict[str, str]  # company_id -> error_message


