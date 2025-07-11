from strenum import StrEnum


class StatementType(StrEnum):
    """The type of financial statement"""

    balance_sheet = "balance_sheet"
    income_statement = "income_statement"
    cashflow = "cashflow"
