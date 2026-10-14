from collections.abc import Iterable

from kfinance.domains.ownership.ownership_models import (
    CompanyOwners,
    HoldingsResult,
    InsiderTradesResult,
)


FIRST_APPEARANCE_NOTE = (
    "When an owner has no prior period to compare against, percent_shares_changed is null and "
    "shares_changed equals shares_held. This means the owner newly appears in the data, not that "
    "it bought its whole position during the period."
)

OWNER_TYPE_BREAKDOWN_NOTE = (
    "The owner types in by_owner_type are mutually exclusive, so their shares_held sum to the "
    "company's shares outstanding, with 'Public and Other' holding whatever the named owner types "
    "don't."
)

OWNERSHIP_PCT_OUT_OF_RANGE_NOTE = (
    "institutional_ownership_pct is not clamped to 0-100, and by_owner_type shares_held can be "
    "negative: the source data has values above 100 and below 0 for a small number of companies."
)

UNMAPPED_HOLDING_NOTE = (
    "A null held_company_id and held_company_name means the held security isn't mapped to a "
    "company (e.g. ETFs, indices, fixed income, or other non-equity securities)."
)

NO_TICKER_NOTE = (
    "A null ticker means the held security has no listed ticker (e.g. private or unlisted "
    "securities, or debt instruments)."
)

MULTI_DAY_TRADE_NOTE = (
    "When a single record covers trades made over several days, trade_date is the latest of "
    "those days."
)


def owners_notes(results: Iterable[CompanyOwners]) -> list[str]:
    """Return the notes that apply to the owners and ownership summaries being returned."""
    results = list(results)
    owners = [owner for result in results for owner in result.owners]
    summaries = [result.summary for result in results if result.summary is not None]

    notes: list[str] = []
    if any(owner.position.percent_shares_changed is None for owner in owners):
        notes.append(FIRST_APPEARANCE_NOTE)
    if any(summary.by_owner_type for summary in summaries):
        notes.append(OWNER_TYPE_BREAKDOWN_NOTE)
    if any(
        (
            summary.institutional_ownership_pct is not None
            and not 0 <= summary.institutional_ownership_pct <= 100
        )
        or any(owner_type.shares_held < 0 for owner_type in summary.by_owner_type)
        for summary in summaries
    ):
        notes.append(OWNERSHIP_PCT_OUT_OF_RANGE_NOTE)
    return notes


def holdings_notes(results: Iterable[HoldingsResult]) -> list[str]:
    """Return the notes that apply to the holdings being returned."""
    holdings = [holding for result in results for holding in result.holdings]

    notes: list[str] = []
    if any(holding.held_company_id is None for holding in holdings):
        notes.append(UNMAPPED_HOLDING_NOTE)
    if any(position.ticker is None for holding in holdings for position in holding.positions):
        notes.append(NO_TICKER_NOTE)
    return notes


def insider_trades_notes(results: Iterable[InsiderTradesResult]) -> list[str]:
    """Return the notes that apply to the insider trades being returned.

    The API only returns the latest date of a multi-day record, so there's no way to tell which
    records span several days. The note is added whenever any trades are returned.
    """
    if any(result.trades for result in results):
        return [MULTI_DAY_TRADE_NOTE]
    return []
