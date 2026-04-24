from datetime import datetime

from pydantic import BaseModel
from strenum import StrEnum


class KeyDevelopment(BaseModel):
    """A single key development event."""

    key_dev_id: int
    situation: str
    announced_date_utc: datetime
    most_important_date_utc: datetime
    source: str
    company_role: str


class KeyDevsResp(BaseModel):
    """Response containing key developments grouped by category.

    The API returns the following structure:
    {
        "results": {
            "Client Announcements": [...],
            "Earnings Releases": [...]
        },
        "next_time_band": {"start_date": "...", "end_date": "..."},
        "notes": "...",
        "errors": ["There is no data associated with company id <company_id>"]
    }

    - results: Maps category name to a list of KeyDevelopment events
    - next_time_band: Optional pagination info (start_date and end_date for next query)
    - notes: Optional message about truncated results or other information
    - errors: List of error messages from the API (e.g., no data for company)
    """

    results: dict[str, list[KeyDevelopment]]
    next_time_band: dict[str, str] | None = None
    notes: str | None = None
    errors: list[str] = []


class KeyDevCategoryType(StrEnum):
    """Key development category types.

    Optional filter to retrieve only key developments within a specific category.
    If not specified, all categories are returned.

    Available categories:
    - company_forecasts_and_ratings: Company forecasts and ratings
    - announced_or_completed_transactions: Announced or completed transactions
    - potential_transactions: Potential transactions
    - listing_or_trading_related: Listing or trading related
    - potential_red_flags_or_distress_indicators: Potential red flags or distress indicators
    - results_announcements_or_corporate_communications: Results announcements or corporate communications
    - customer_or_product_related: Customer or product related
    - corporate_structure_related: Corporate structure related
    - dividends_or_splits: Dividends or splits
    - bankruptcy_updates: Bankruptcy updates
    - investor_activism: Investor activism
    - transaction_updates: Transaction updates
    """

    COMPANY_FORECASTS_AND_RATINGS = "company_forecasts_and_ratings"
    ANNOUNCED_OR_COMPLETED_TRANSACTIONS = "announced_or_completed_transactions"
    POTENTIAL_TRANSACTIONS = "potential_transactions"
    LISTING_OR_TRADING_RELATED = "listing_or_trading_related"
    POTENTIAL_RED_FLAGS_OR_DISTRESS_INDICATORS = "potential_red_flags_or_distress_indicators"
    RESULTS_ANNOUNCEMENTS_OR_CORPORATE_COMMUNICATIONS = (
        "results_announcements_or_corporate_communications"
    )
    CUSTOMER_OR_PRODUCT_RELATED = "customer_or_product_related"
    CORPORATE_STRUCTURE_RELATED = "corporate_structure_related"
    DIVIDENDS_OR_SPLITS = "dividends_or_splits"
    BANKRUPTCY_UPDATES = "bankruptcy_updates"
    INVESTOR_ACTIVISM = "investor_activism"
    TRANSACTION_UPDATES = "transaction_updates"
