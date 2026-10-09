from datetime import datetime

from pydantic import BaseModel, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from strenum import StrEnum


class KeyDevelopment(BaseModel):
    """A single key development event."""

    key_dev_id: int
    situation: str | None = None
    announced_date_utc: datetime | None = None
    most_important_date_utc: datetime | None = None
    source: str | None = None
    company_role: str | None = None
    has_transcript: bool | None = None


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
    next_time_band: dict[str, str | None] | None = None
    notes: str | None = None
    errors: list[str] = []


class DescribedStrEnum(StrEnum):
    """StrEnum whose members can carry a short description, e.g. ``A = ("a", "what a covers")``.

    The member descriptions are appended to the enum's description in the JSON schema that tools
    send to the model, so each value is explained next to the field that uses it.
    """

    description: str

    def __new__(cls, value: str, description: str = "") -> "DescribedStrEnum":
        """Create a member from its string value and an optional description."""
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.description = description
        return obj

    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler.resolve_ref_schema(handler(schema))
        explained = "; ".join(f"{m.value}={m.description}" for m in cls if m.description)
        json_schema["description"] = f"{(cls.__doc__ or '').strip()} {explained}".strip()
        return json_schema


class KeyDevCategoryType(DescribedStrEnum):
    """Topic filter. Null for broad requests (one call, not one per category)."""

    COMPANY_FORECASTS_AND_RATINGS = ("company_forecasts_and_ratings", "guidance changes")
    ANNOUNCED_OR_COMPLETED_TRANSACTIONS = (
        "announced_or_completed_transactions",
        "M&A, buybacks, offerings, IPOs, spin-offs",
    )
    POTENTIAL_TRANSACTIONS = ("potential_transactions", "rumors, strategic alternatives")
    LISTING_OR_TRADING_RELATED = (
        "listing_or_trading_related",
        "delistings, index, ticker and exchange changes",
    )
    POTENTIAL_RED_FLAGS_OR_DISTRESS_INDICATORS = (
        "potential_red_flags_or_distress_indicators",
        "lawsuits, probes, restatements, defaults",
    )
    RESULTS_ANNOUNCEMENTS_OR_CORPORATE_COMMUNICATIONS = (
        "results_announcements_or_corporate_communications",
        "earnings, calls, presentations, shareholder meetings",
    )
    CUSTOMER_OR_PRODUCT_RELATED = (
        "customer_or_product_related",
        "client wins, launches, alliances",
    )
    CORPORATE_STRUCTURE_RELATED = (
        "corporate_structure_related",
        "executive and board changes, reorganizations",
    )
    DIVIDENDS_OR_SPLITS = "dividends_or_splits"
    BANKRUPTCY_UPDATES = "bankruptcy_updates"
    INVESTOR_ACTIVISM = "investor_activism"
    TRANSACTION_UPDATES = ("transaction_updates", "buyback plan changes")


class KeyDevEventType(DescribedStrEnum):
    """One kind of call or presentation; do not combine with key_dev_category. Earnings calls are not included."""

    COMPANY_CONFERENCE_PRESENTATION = ("company_conference_presentation", "investor conferences")
    SHAREHOLDER_ANALYST_CALL = (
        "shareholder_analyst_call",
        "shareholder meetings, analyst briefings",
    )
    SPECIAL_CALL = ("special_call", "a specific announcement such as a partnership")
    MNA_CALL = "mna_call"
    ANALYST_INVESTOR_DAY = ("analyst_investor_day", "a company's own investor day")
    SALES_TRADING_STATEMENT_CALL = "sales_trading_statement_call"
    GUIDANCE_UPDATE_CALL = "guidance_update_call"
    INTERIM_MANAGEMENT_STATEMENT_CALL = "interim_management_statement_call"
    OPERATING_RESULTS_CALL = "operating_results_call"
    FIXED_INCOME_CALL = ("fixed_income_call", "debt investors")
