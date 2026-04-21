from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel


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

    # TODO: check structure once server side changes go through.
    The API returns the following structure:
    {
        "results": {
            "Client Announcements": [...],
            "Earnings Releases": [...]
        },
        "next_time_band": {"start_date": "...", "end_date": "..."},
        "notes": "..."
    }

    - results: Maps category name to a list of KeyDevelopment events
    - next_time_band: Optional pagination info (start_date and end_date for next query)
    - notes: Optional message about truncated results or other information
    """

    results: dict[str, list[KeyDevelopment]]
    next_time_band: dict[str, str] | None = None
    notes: str | None = None


class KeyDevCategoryType(IntEnum):
    """Key development category types.

    Optional filter to retrieve only key developments within a specific category.
    If not specified, all categories are returned.

    Available categories:
    - 1: Company forecasts and ratings
    - 2: Announced or completed transactions
    - 3: Potential transactions
    - 4: Listing or trading related
    - 5: Potential red flags or distress indicators
    - 6: Results announcements or corporate communications
    - 7: Customer or product related
    - 8: Corporate structure related
    - 10: Dividends or splits
    - 12: Bankruptcy updates
    - 13: Investor activism
    - 15: Transaction updates
    """

    COMPANY_FORECASTS_AND_RATINGS = 1
    ANNOUNCED_OR_COMPLETED_TRANSACTIONS = 2
    POTENTIAL_TRANSACTIONS = 3
    LISTING_OR_TRADING_RELATED = 4
    POTENTIAL_RED_FLAGS_OR_DISTRESS_INDICATORS = 5
    RESULTS_ANNOUNCEMENTS_OR_CORPORATE_COMMUNICATIONS = 6
    CUSTOMER_OR_PRODUCT_RELATED = 7
    CORPORATE_STRUCTURE_RELATED = 8
    DIVIDENDS_OR_SPLITS = 10
    BANKRUPTCY_UPDATES = 12
    INVESTOR_ACTIVISM = 13
    TRANSACTION_UPDATES = 15
