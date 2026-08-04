from strenum import StrEnum


class DatasetFilter(StrEnum):
    """Dataset filters.

    These values are passed as the `datasets_filter` parameter to the /ids endpoint
    to scope entity resolution to specific datasets.
    """

    RATINGS = "ratings"
    TRANSACTIONS_MA = "transactions"
    PRIVATE_COMPANY_FINANCIALS = "private_company_financials"
