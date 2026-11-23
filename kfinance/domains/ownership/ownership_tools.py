from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from textwrap import dedent
from typing import Any, Type

import httpx2
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.companies.company_models import IdentificationTripleWithCompanyInfo
from kfinance.domains.ownership.ownership_models import (
    HELD_COMPANY_TYPES_BY_CATEGORY,
    INSIDER_TRANSACTION_TYPES_BY_CATEGORY,
    OWNER_TYPES_BY_CATEGORY,
    CompanyInsiderTrades,
    CompanyOwners,
    FundsView,
    HeldCompanyTypeCategory,
    HoldingsCoverage,
    HoldingsResp,
    InsiderTradesResp,
    InsiderTradesSortBy,
    InsiderTransactionCategory,
    OwnerHoldings,
    OwnersCoverage,
    OwnersResp,
    OwnersSortBy,
    OwnersSummary,
    OwnersSummaryResp,
    OwnerTypeCategory,
    PositionChange,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithIdInfoAndErrors,
)


# The default number of owners, holdings or trades returned per identifier.
DEFAULT_LIMIT = 100

# Below these, the Ownership dataset's coverage of a company is considered low, and the tool
# response points the caller to the corporate tree tools.
LOW_OWNERS_COVERAGE_PCT = 50
LOW_HOLDINGS_COVERAGE_COUNT = 5

LIMIT_DESCRIPTION = (
    "Maximum {items} returned per identifier; omit for the default "
    f"{DEFAULT_LIMIT}. Set null only when the user explicitly requests an exhaustive answer "
    '("all", "every", "full", "complete"); null can produce a very large response.'
)

OWNER_PERSON_IDS_DESCRIPTION = (
    "Only return {items} made by these people, by person_id. Get person_ids from "
    "get_professionals_from_identifiers (e.g. for a company's CEO or directors)."
)

FIRST_APPEARANCE_NOTE = (
    "When an owner has no prior period to compare against, percent_shares_changed is null and "
    "shares_changed equals shares_held. This means the owner newly appears in the data, not that "
    "it bought its whole position during the period."
)

OWNERSHIP_PCT_OUT_OF_RANGE_NOTE = (
    "institutional_ownership_pct is not clamped to 0-100, and by_owner_type shares_held can be "
    "negative: the source data has values above 100 and below 0 for a small number of companies."
)

_LOW_COVERAGE_NOTE = (
    "{identifier}: The ownership coverage in this dataset is low ({detail}). The dataset is built "
    "from public filings, so it often misses {missing} private companies that don't file public "
    "reports. Use {tool} to find {controlling}. The corporate tree tools only include "
    "controlling (50% or more) relationships, not minority stakes."
)


def owners_low_coverage_note(identifier: str, coverage: OwnersCoverage) -> str | None:
    """Return a note pointing to the corporate tree tools when the owners coverage is low."""
    pct = coverage.total_pct_shares_outstanding
    if coverage.total_owners == 0:
        detail = "no owners found"
    elif pct is None:
        detail = "no owner has a known percent of shares outstanding"
    elif pct < LOW_OWNERS_COVERAGE_PCT:
        detail = f"the owners found hold {pct:.1f}% of shares outstanding"
    else:
        return None
    return _LOW_COVERAGE_NOTE.format(
        identifier=identifier,
        detail=detail,
        missing="owners that are",
        tool="get_ultimate_parent_paths_from_identifiers",
        controlling="the company's parent companies",
    )


def holdings_low_coverage_note(identifier: str, coverage: HoldingsCoverage) -> str | None:
    """Return a note pointing to the corporate tree tools when the holdings coverage is low."""
    if coverage.total_held_companies == 0:
        detail = "no holdings found"
    elif coverage.total_pct_portfolio is None:
        detail = "no holding has a known percent of portfolio"
    elif coverage.total_held_companies < LOW_HOLDINGS_COVERAGE_COUNT:
        detail = f"only {coverage.total_held_companies} held companies found"
    else:
        return None
    return _LOW_COVERAGE_NOTE.format(
        identifier=identifier,
        detail=detail,
        missing="stakes in",
        tool="search_corporate_tree_from_identifiers",
        controlling="the companies it controls, like subsidiaries",
    )


def truncation_note(identifier: str, num_returned: int, num_total: int, items: str) -> str:
    """Return a note saying that only num_returned of num_total items were returned."""
    return (
        f"{identifier}: returned {num_returned} of {num_total:,} matching {items}. "
        "Set a higher limit, or null for no limit, to see more."
    )


def summary_out_of_range(summary: OwnersSummary) -> bool:
    """Whether the summary has an ownership percent outside 0-100 or negative shares held."""
    pct = summary.institutional_ownership_pct
    return (pct is not None and not 0 <= pct <= 100) or any(
        owner_type.shares_held < 0 for owner_type in summary.by_owner_type
    )


@dataclass
class ResolvedIdentifiers:
    """The identifiers of a tool call resolved together with its filter identifiers.

    Attributes:
        id_triples: The resolved (primary) identifiers.
        filter_company_ids: The company ids of the resolved filter identifiers, or None when no
            filter identifiers were passed.
        errors: The resolution errors, by identifier.
    """

    id_triples: dict[str, IdentificationTripleWithCompanyInfo]
    filter_company_ids: list[int] | None
    errors: dict[str, list[str]]


async def resolve_identifiers_and_filter_identifiers(
    identifiers: list[str],
    filter_identifiers: list[str] | None,
    httpx_client: httpx2.AsyncClient,
) -> ResolvedIdentifiers:
    """Resolve the identifiers and the filter identifiers (e.g. owner companies) in one call."""
    all_identifiers = list(dict.fromkeys(identifiers + (filter_identifiers or [])))
    id_triple_resp = await unified_fetch_id_triples(
        identifiers=all_identifiers, httpx_client=httpx_client
    )
    triples = id_triple_resp.identifiers_to_id_triples

    errors: dict[str, list[str]] = defaultdict(list)
    for identifier, error in id_triple_resp.errors.items():
        errors[identifier].append(error)

    filter_company_ids = None
    if filter_identifiers is not None:
        filter_company_ids = list(
            dict.fromkeys(
                triples[identifier].company_id
                for identifier in filter_identifiers
                if identifier in triples
            )
        )

    return ResolvedIdentifiers(
        id_triples={
            identifier: triples[identifier] for identifier in identifiers if identifier in triples
        },
        filter_company_ids=filter_company_ids,
        errors=errors,
    )


def combine_owner_ids(
    company_ids: list[int] | None, person_ids: list[int] | None
) -> list[int] | None:
    """Combine owner company and person ids into the API's owner_ids, or None for no filter."""
    if company_ids is None and person_ids is None:
        return None
    return list(dict.fromkeys((company_ids or []) + (person_ids or [])))


def unresolved_filter_error(param_names: str) -> str:
    """Return the error for an id filter whose identifiers all failed to resolve."""
    return f"None of the {param_names} could be resolved, so no data was fetched."


def add_unique_error(errors: dict[str, list[str]], identifier: str, error: str) -> None:
    """Add an error for the identifier, unless it was already reported."""
    if error not in errors[identifier]:
        errors[identifier].append(error)


class GetOwnersFromIdentifiersArgs(ToolArgsWithIdentifiers):
    owner_type: OwnerTypeCategory = Field(
        default=OwnerTypeCategory.all,
        description="Only return owners of this type: 'institutions' (asset managers, banks, hedge funds, VC/PE firms, sovereign wealth funds), 'individuals' (insiders and other people), 'corporations' (public and private companies), 'other' (company-controlled foundations, ESOPs, state-owned entities), or 'all'. Only allowed with funds_view='exclude_funds'.",
    )
    position_changes: list[PositionChange] | None = Field(
        default=None,
        min_length=1,
        description="Only return owners whose position changed in any of these ways during the latest reporting period, relative to the one before it: 'bought' (increased), 'sold' (decreased), 'new' (newly appears in the data), or 'closed' (fully exited). The changes overlap: a new position also counts as bought, and a closed one as sold. Omit for all owners.",
    )
    owner_company_identifiers: list[str] | None = Field(
        default=None,
        min_length=1,
        description="Only return these owners that are companies, as tickers, company names, or company_ids (e.g. 'C_12345'). Use to check how much of a company a specific investor owns.",
    )
    owner_person_ids: list[int] | None = Field(
        default=None,
        min_length=1,
        description="Only return these owners that are people, by person_id. Get person_ids from get_professionals_from_identifiers.",
    )
    min_pct_shares_outstanding: float | None = Field(
        default=None,
        ge=0,
        description="Only return owners holding at least this percent of the company's shares outstanding (e.g. 5 for 5%). Owners with an unknown percent are dropped.",
    )
    funds_view: FundsView = Field(
        default=FundsView.exclude_funds,
        description="'exclude_funds' (default) to leave out funds whose shares are already counted in their sponsor's or advisor's position, 'include_funds' to also return them, or 'funds_only' to only return them.",
    )
    sort_by: OwnersSortBy = Field(
        default=OwnersSortBy.shares_held,
        description="'shares_held' (default) for the largest owners first, or 'absolute_shares_changed' for the largest purchases and sales during the latest reporting period first.",
    )
    limit: int | None = Field(
        default=DEFAULT_LIMIT, ge=1, description=LIMIT_DESCRIPTION.format(items="owners")
    )
    include_summary: bool = Field(
        default=False,
        description="Also return the company's aggregate ownership summary (institutional ownership %, number of holders, buyers/sellers, and shares held by owner type).",
    )

    @model_validator(mode="after")
    def validate_owner_type_with_funds_view(self) -> Self:
        """Reject an owner_type with funds, which have no owner type."""
        if self.owner_type != OwnerTypeCategory.all and self.funds_view != FundsView.exclude_funds:
            raise ValueError(
                "owner_type can only be combined with funds_view='exclude_funds': funds have no "
                "owner type."
            )
        return self


class GetOwnersFromIdentifiersResp(ToolRespWithIdInfoAndErrors[CompanyOwners]):
    # None rather than an empty list when no notes apply, so that the field is dropped from
    # tool output (serialized with exclude_none=True).
    notes: list[str] | None = None


class GetOwnersFromIdentifiers(KfinanceTool):
    name: str = "get_owners_from_identifiers"
    description: str = dedent("""
        Get the owners (shareholders) of a list of companies from public ownership filings. Each owner includes the owner name and id, owner type, institution type, shares held, percent of shares outstanding, holding date, reporting period, and period_change (shares bought or sold during the latest reporting period). Results include total_matching, the number of owners matching the filters before the limit.

        - Only the latest reporting period is returned: each owner's current position, and period_change relative to the reporting period before it. Ownership as of earlier periods, or changes over longer spans, isn't available. The latest period can still be open, so its end_date can be in the future.
        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - Pass a ticker as given. Otherwise pass the company's full name with its legal suffix (e.g. "Apple Inc." rather than "Apple").
        - The identifiers are the companies being owned. To find what a company or fund owns (its portfolio), use get_holdings_from_identifiers instead.
        - Funds are excluded by default because their shares are usually also counted in the position of their sponsor or investment advisor (e.g. BlackRock, Inc.). Fund rows have a fund_parent; don't add them to other owners' totals.
        - A null percent_shares_changed means the owner newly appears in the data.
        - position_changes keeps owners matching any of the given changes, and the changes overlap: a new position also counts as bought, and a closed one as sold. Use ["new"] for only new positions, not ["bought"].
        - To filter to specific owners, pass owner_company_identifiers for companies, and owner_person_ids (from get_professionals_from_identifiers) for people.
        - Set include_summary=True for aggregate ownership questions: institutional ownership percentage, number of institutional holders, number of buyers/sellers/new buyers/closed positions, shares bought/sold, or shares held by owner type.

        Examples:
        Query: "Who are the largest shareholders of Apple?"
        Function: get_owners_from_identifiers(identifiers=["Apple Inc."], limit=10)

        Query: "Which institutions own more than 5% of SPGI and MSFT?"
        Function: get_owners_from_identifiers(identifiers=["SPGI", "MSFT"], owner_type="institutions", min_pct_shares_outstanding=5)

        Query: "Which institutions sold the most AAPL most recently?"
        Function: get_owners_from_identifiers(identifiers=["AAPL"], owner_type="institutions", position_changes=["sold"], sort_by="absolute_shares_changed", limit=10)

        Query: "Who initiated new positions in NVDA?"
        Function: get_owners_from_identifiers(identifiers=["NVDA"], position_changes=["new"])

        Query: "Which institutions opened or exited positions in MSFT?"
        Function: get_owners_from_identifiers(identifiers=["MSFT"], owner_type="institutions", position_changes=["new", "closed"])

        Query: "How much NVIDIA does BlackRock own?"
        Function: get_owners_from_identifiers(identifiers=["NVDA"], owner_company_identifiers=["BlackRock, Inc."])

        Query: "What percent of Tesla is owned by institutions?"
        Function: get_owners_from_identifiers(identifiers=["Tesla, Inc."], include_summary=True, limit=10)

        Query: "How much Tesla stock does its CEO own?"
        Function 1: get_professionals_from_identifiers(identifiers=["Tesla, Inc."], professional_type="employees", timeframe="current")
        # Function 1 returns Tesla's current employees. Extract the <person_id> for the CEO.
        Function 2: get_owners_from_identifiers(identifiers=["Tesla, Inc."], owner_person_ids=[<person_id>])
    """).strip()
    args_schema: Type[BaseModel] = GetOwnersFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.OwnershipPermission}

    async def _arun(
        self,
        identifiers: list[str],
        owner_type: OwnerTypeCategory = OwnerTypeCategory.all,
        position_changes: list[PositionChange] | None = None,
        owner_company_identifiers: list[str] | None = None,
        owner_person_ids: list[int] | None = None,
        min_pct_shares_outstanding: float | None = None,
        funds_view: FundsView = FundsView.exclude_funds,
        sort_by: OwnersSortBy = OwnersSortBy.shares_held,
        limit: int | None = DEFAULT_LIMIT,
        include_summary: bool = False,
    ) -> GetOwnersFromIdentifiersResp:
        """"""
        return await get_owners_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
            owner_type=owner_type,
            position_changes=position_changes,
            owner_company_identifiers=owner_company_identifiers,
            owner_person_ids=owner_person_ids,
            min_pct_shares_outstanding=min_pct_shares_outstanding,
            funds_view=funds_view,
            sort_by=sort_by,
            limit=limit,
            include_summary=include_summary,
        )


class GetHoldingsFromIdentifiersArgs(ToolArgsWithIdentifiers):
    held_company_type: HeldCompanyTypeCategory = Field(
        default=HeldCompanyTypeCategory.all,
        description="Only return holdings of companies of this type: 'public_companies', 'private_companies', 'funds' (public and private funds, fund families), 'investment_firms' (investment firms and investment arms), 'other' (e.g. government and educational institutions, indexes), or 'all'. Securities not mapped to a company are only returned with 'all'.",
    )
    held_company_identifiers: list[str] | None = Field(
        default=None,
        min_length=1,
        description="Only return holdings of these companies, as tickers, company names, or company_ids. Use to check whether, or how much, an owner holds of specific companies.",
    )
    min_pct_portfolio: float | None = Field(
        default=None,
        ge=0,
        description="Only return holdings that make up at least this percent of the owner's portfolio (e.g. 5 for 5%), summed across the held company's securities. Holdings with an unknown percent are dropped.",
    )
    min_pct_shares_outstanding: float | None = Field(
        default=None,
        ge=0,
        description="Only return holdings where the owner holds at least this percent of the held company's shares outstanding (e.g. 5 for 5%) in at least one security. Holdings with an unknown percent are dropped.",
    )
    limit: int | None = Field(
        default=DEFAULT_LIMIT, ge=1, description=LIMIT_DESCRIPTION.format(items="held companies")
    )


class GetHoldingsFromIdentifiersResp(ToolRespWithIdInfoAndErrors[OwnerHoldings]):
    notes: list[str] | None = None


class GetHoldingsFromIdentifiers(KfinanceTool):
    name: str = "get_holdings_from_identifiers"
    description: str = dedent("""
        Get the holdings (portfolio) of a list of owners (e.g. asset managers, funds, or other companies) from public ownership filings. The identifiers are the owners, not the companies being held. Each holding lists the held company id, name and type, its total percent of the owner's portfolio, and the owner's positions in the held company's securities (ticker, shares held, percent of portfolio, percent of shares outstanding, and holding date). Holdings are ordered by total percent of portfolio, largest first. Results include total_matching, the number of holdings matching the filters before the limit.

        - Only the owner's latest reported holdings are returned; holdings as of earlier periods aren't available.
        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - Pass a ticker as given. Otherwise pass the owner's full name with its legal suffix (e.g. "The Vanguard Group, Inc." rather than "Vanguard"). Short or informal names of asset managers can resolve to the wrong entity.
        - To find who owns a company, use get_owners_from_identifiers instead.

        Examples:
        Query: "What are Berkshire Hathaway's largest holdings?"
        Function: get_holdings_from_identifiers(identifiers=["Berkshire Hathaway Inc."], limit=10)

        Query: "What share of Berkshire Hathaway's portfolio is in Apple?"
        Function: get_holdings_from_identifiers(identifiers=["Berkshire Hathaway Inc."], held_company_identifiers=["AAPL"])

        Query: "Which positions make up more than 5% of Pershing Square's portfolio?"
        Function: get_holdings_from_identifiers(identifiers=["Pershing Square Capital Management, L.P."], min_pct_portfolio=5)

        Query: "Which public companies does BlackRock own more than 10% of?"
        Function: get_holdings_from_identifiers(identifiers=["BlackRock, Inc."], held_company_type="public_companies", min_pct_shares_outstanding=10)

        Query: "Compare the top 5 holdings of BlackRock and Vanguard"
        Function: get_holdings_from_identifiers(identifiers=["BlackRock, Inc.", "The Vanguard Group, Inc."], limit=5)
    """).strip()
    args_schema: Type[BaseModel] = GetHoldingsFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.OwnershipPermission}

    async def _arun(
        self,
        identifiers: list[str],
        held_company_type: HeldCompanyTypeCategory = HeldCompanyTypeCategory.all,
        held_company_identifiers: list[str] | None = None,
        min_pct_portfolio: float | None = None,
        min_pct_shares_outstanding: float | None = None,
        limit: int | None = DEFAULT_LIMIT,
    ) -> GetHoldingsFromIdentifiersResp:
        """"""
        return await get_holdings_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
            held_company_type=held_company_type,
            held_company_identifiers=held_company_identifiers,
            min_pct_portfolio=min_pct_portfolio,
            min_pct_shares_outstanding=min_pct_shares_outstanding,
            limit=limit,
        )


class GetInsiderTradesFromIdentifiersArgs(ToolArgsWithIdentifiers):
    start_date: date | None = Field(
        default=None,
        description="Only return trades made on or after this date (YYYY-MM-DD format).",
    )
    end_date: date | None = Field(
        default=None,
        description="Only return trades made on or before this date (YYYY-MM-DD format).",
    )
    transaction_type: InsiderTransactionCategory = Field(
        default=InsiderTransactionCategory.all,
        description="'acquisition' for purchases and other acquisitions (including option exercises and awards), 'disposition' for sales and other dispositions, or 'all'. Form 3 holdings statements and Form 144 intents to sell are only returned with 'all'.",
    )
    owner_company_identifiers: list[str] | None = Field(
        default=None,
        min_length=1,
        description="Only return trades made by these insiders that are companies, as tickers, company names, or company_ids.",
    )
    insider_person_ids: list[int] | None = Field(
        default=None,
        min_length=1,
        description="Only return trades made by these insiders that are people, by person_id. Get person_ids from get_professionals_from_identifiers (e.g. for a company's CEO or directors).",
    )
    min_absolute_transaction_value_usd: float | None = Field(
        default=None,
        ge=0,
        description="Only return trades with an absolute transaction value of at least this many USD, so large sales pass as well as large purchases. Trades with an unknown value are dropped.",
    )
    sort_by: InsiderTradesSortBy = Field(
        default=InsiderTradesSortBy.date,
        description="'date' (default) for the most recent trades first, 'absolute_transaction_value_usd' for the largest trades by value first, or 'absolute_shares' for the largest trades by shares first.",
    )
    limit: int | None = Field(
        default=DEFAULT_LIMIT, ge=1, description=LIMIT_DESCRIPTION.format(items="trades")
    )

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        """Reject a start_date after the end_date, which would match no trades."""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError(
                f"start_date ({self.start_date}) must be on or before end_date ({self.end_date})."
            )
        return self


class GetInsiderTradesFromIdentifiersResp(ToolRespWithIdInfoAndErrors[CompanyInsiderTrades]):
    notes: list[str] | None = None


class GetInsiderTradesFromIdentifiers(KfinanceTool):
    name: str = "get_insider_trades_from_identifiers"
    description: str = dedent("""
        Get the insider trades (trades by officers, directors, and other insiders filed with the SEC) for a list of companies. Each trade includes the insider name and owner_id, transaction type, security type, number of shares, min and max price per share, transaction value in USD, trade date, and filing date. Results include total_matching, the number of trades matching the filters before the limit.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - Pass a ticker as given. Otherwise pass the company's full name with its legal suffix (e.g. "NVIDIA Corporation" rather than "Nvidia").
        - shares is negative for dispositions (e.g. sales).
        - To filter to specific insiders, pass insider_person_ids for people, using the person_ids from get_professionals_from_identifiers, and owner_company_identifiers for companies.

        Examples:
        Query: "Show me recent insider trades at Nvidia"
        Function: get_insider_trades_from_identifiers(identifiers=["NVIDIA Corporation"], limit=20)

        Query: "Did insiders at AAPL or MSFT sell stock in 2024?"
        Function: get_insider_trades_from_identifiers(identifiers=["AAPL", "MSFT"], start_date="2024-01-01", end_date="2024-12-31", transaction_type="disposition")

        Query: "What were the largest insider purchases at Meta since January 2025?"
        Function: get_insider_trades_from_identifiers(identifiers=["META"], start_date="2025-01-01", transaction_type="acquisition", sort_by="absolute_transaction_value_usd", limit=10)

        Query: "Which insider trades at Tesla were worth more than $10M?"
        Function: get_insider_trades_from_identifiers(identifiers=["TSLA"], min_absolute_transaction_value_usd=10000000)

        Query: "What were the insider trades of Microsoft's CEO in 2024?"
        Function 1: get_professionals_from_identifiers(identifiers=["MSFT"], professional_type="employees", timeframe="current")
        # Function 1 returns Microsoft's current employees. Extract the <person_id> for the CEO.
        Function 2: get_insider_trades_from_identifiers(identifiers=["MSFT"], insider_person_ids=[<person_id>], start_date="2024-01-01", end_date="2024-12-31")
    """).strip()
    args_schema: Type[BaseModel] = GetInsiderTradesFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.OwnershipPermission}

    async def _arun(
        self,
        identifiers: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
        transaction_type: InsiderTransactionCategory = InsiderTransactionCategory.all,
        owner_company_identifiers: list[str] | None = None,
        insider_person_ids: list[int] | None = None,
        min_absolute_transaction_value_usd: float | None = None,
        sort_by: InsiderTradesSortBy = InsiderTradesSortBy.date,
        limit: int | None = DEFAULT_LIMIT,
    ) -> GetInsiderTradesFromIdentifiersResp:
        """"""
        return await get_insider_trades_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
            start_date=start_date,
            end_date=end_date,
            transaction_type=transaction_type,
            owner_company_identifiers=owner_company_identifiers,
            insider_person_ids=insider_person_ids,
            min_absolute_transaction_value_usd=min_absolute_transaction_value_usd,
            sort_by=sort_by,
            limit=limit,
        )


async def get_owners_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx2.AsyncClient,
    owner_type: OwnerTypeCategory = OwnerTypeCategory.all,
    position_changes: list[PositionChange] | None = None,
    owner_company_identifiers: list[str] | None = None,
    owner_person_ids: list[int] | None = None,
    min_pct_shares_outstanding: float | None = None,
    funds_view: FundsView = FundsView.exclude_funds,
    sort_by: OwnersSortBy = OwnersSortBy.shares_held,
    limit: int | None = DEFAULT_LIMIT,
    include_summary: bool = False,
) -> GetOwnersFromIdentifiersResp:
    """Fetch owners (and optionally the ownership summary) for all identifiers."""
    resolved = await resolve_identifiers_and_filter_identifiers(
        identifiers=identifiers,
        filter_identifiers=owner_company_identifiers,
        httpx_client=httpx_client,
    )
    errors = resolved.errors
    owner_ids = combine_owner_ids(resolved.filter_company_ids, owner_person_ids)

    if owner_ids == []:
        # Without this, the API would get no owner_ids filter and return every owner.
        for identifier in resolved.id_triples:
            errors[identifier].append(unresolved_filter_error("owner_company_identifiers"))
        return GetOwnersFromIdentifiersResp(
            identifier_results={},
            identifier_errors=errors,
            identifier_info=resolved.id_triples,
        )

    owners_tasks = [
        AsyncTask(
            func=fetch_owners_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                httpx_client=httpx_client,
                owner_type=owner_type,
                position_changes=position_changes,
                owner_ids=owner_ids,
                min_pct_shares_outstanding=min_pct_shares_outstanding,
                funds_view=funds_view,
                sort_by=sort_by,
                limit=limit,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in resolved.id_triples.items()
    ]
    summary_tasks = (
        [
            AsyncTask(
                func=fetch_owners_summary_from_company_id,
                kwargs=dict(company_id=id_triple.company_id, httpx_client=httpx_client),
                result_key=identifier,
            )
            for identifier, id_triple in resolved.id_triples.items()
        ]
        if include_summary
        else []
    )

    await batch_execute_async_tasks(tasks=owners_tasks + summary_tasks)

    results: dict[str, CompanyOwners] = {}
    truncation_notes: list[str] = []
    coverage_notes: list[str] = []
    for owners_task in owners_tasks:
        identifier = owners_task.result_key
        if owners_task.error:
            errors[identifier].append(owners_task.error)
            continue
        owners_resp: OwnersResp = owners_task.result
        errors[identifier].extend(owners_resp.errors.values())
        owners_result = owners_resp.results
        if owners_result.coverage is not None and (
            note := owners_low_coverage_note(identifier, owners_result.coverage)
        ):
            coverage_notes.append(note)
        if owners_result.owners:
            results[identifier] = CompanyOwners(
                owners=owners_result.owners, total_matching=owners_result.total_matching
            )
            if owners_result.total_matching > len(owners_result.owners):
                truncation_notes.append(
                    truncation_note(
                        identifier,
                        len(owners_result.owners),
                        owners_result.total_matching,
                        "owners",
                    )
                )

    for summary_task in summary_tasks:
        identifier = summary_task.result_key
        if summary_task.error:
            # Skip errors that the owners call already reported, like a request error that both
            # calls hit.
            add_unique_error(errors, identifier, summary_task.error)
            continue
        summary_resp: OwnersSummaryResp = summary_task.result
        for error in summary_resp.errors.values():
            add_unique_error(errors, identifier, error)
        if summary_resp.results is not None:
            results.setdefault(identifier, CompanyOwners()).summary = summary_resp.results

    notes = list(truncation_notes)
    if any(
        owner.period_change.percent_shares_changed is None
        for result in results.values()
        for owner in result.owners
    ):
        notes.append(FIRST_APPEARANCE_NOTE)
    if any(
        result.summary is not None and summary_out_of_range(result.summary)
        for result in results.values()
    ):
        notes.append(OWNERSHIP_PCT_OUT_OF_RANGE_NOTE)
    notes.extend(coverage_notes)

    return GetOwnersFromIdentifiersResp(
        identifier_results=results,
        identifier_errors=errors,
        identifier_info=resolved.id_triples,
        notes=notes or None,
    )


async def get_holdings_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx2.AsyncClient,
    held_company_type: HeldCompanyTypeCategory = HeldCompanyTypeCategory.all,
    held_company_identifiers: list[str] | None = None,
    min_pct_portfolio: float | None = None,
    min_pct_shares_outstanding: float | None = None,
    limit: int | None = DEFAULT_LIMIT,
) -> GetHoldingsFromIdentifiersResp:
    """Fetch portfolio holdings for all identifiers."""
    resolved = await resolve_identifiers_and_filter_identifiers(
        identifiers=identifiers,
        filter_identifiers=held_company_identifiers,
        httpx_client=httpx_client,
    )
    errors = resolved.errors

    if resolved.filter_company_ids == []:
        # Without this, the API would get no held_company_ids filter and return every holding.
        for identifier in resolved.id_triples:
            errors[identifier].append(unresolved_filter_error("held_company_identifiers"))
        return GetHoldingsFromIdentifiersResp(
            identifier_results={},
            identifier_errors=errors,
            identifier_info=resolved.id_triples,
        )

    tasks = [
        AsyncTask(
            func=fetch_holdings_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                httpx_client=httpx_client,
                held_company_type=held_company_type,
                held_company_ids=resolved.filter_company_ids,
                min_pct_portfolio=min_pct_portfolio,
                min_pct_shares_outstanding=min_pct_shares_outstanding,
                limit=limit,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in resolved.id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, OwnerHoldings] = {}
    truncation_notes: list[str] = []
    coverage_notes: list[str] = []
    for task in tasks:
        identifier = task.result_key
        if task.error:
            errors[identifier].append(task.error)
            continue
        resp: HoldingsResp = task.result
        errors[identifier].extend(resp.errors.values())
        holdings_result = resp.results
        if holdings_result.coverage is not None and (
            note := holdings_low_coverage_note(identifier, holdings_result.coverage)
        ):
            coverage_notes.append(note)
        if holdings_result.holdings:
            results[identifier] = OwnerHoldings(
                holdings=holdings_result.holdings, total_matching=holdings_result.total_matching
            )
            if holdings_result.total_matching > len(holdings_result.holdings):
                truncation_notes.append(
                    truncation_note(
                        identifier,
                        len(holdings_result.holdings),
                        holdings_result.total_matching,
                        "held companies",
                    )
                )

    return GetHoldingsFromIdentifiersResp(
        identifier_results=results,
        identifier_errors=errors,
        identifier_info=resolved.id_triples,
        notes=truncation_notes + coverage_notes or None,
    )


async def get_insider_trades_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx2.AsyncClient,
    start_date: date | None = None,
    end_date: date | None = None,
    transaction_type: InsiderTransactionCategory = InsiderTransactionCategory.all,
    owner_company_identifiers: list[str] | None = None,
    insider_person_ids: list[int] | None = None,
    min_absolute_transaction_value_usd: float | None = None,
    sort_by: InsiderTradesSortBy = InsiderTradesSortBy.date,
    limit: int | None = DEFAULT_LIMIT,
) -> GetInsiderTradesFromIdentifiersResp:
    """Fetch insider trades for all identifiers."""
    resolved = await resolve_identifiers_and_filter_identifiers(
        identifiers=identifiers,
        filter_identifiers=owner_company_identifiers,
        httpx_client=httpx_client,
    )
    errors = resolved.errors
    owner_ids = combine_owner_ids(resolved.filter_company_ids, insider_person_ids)

    if owner_ids == []:
        # Without this, the API would get no owner_ids filter and return every trade.
        for identifier in resolved.id_triples:
            errors[identifier].append(unresolved_filter_error("owner_company_identifiers"))
        return GetInsiderTradesFromIdentifiersResp(
            identifier_results={},
            identifier_errors=errors,
            identifier_info=resolved.id_triples,
        )

    tasks = [
        AsyncTask(
            func=fetch_insider_trades_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                httpx_client=httpx_client,
                start_date=start_date,
                end_date=end_date,
                transaction_type=transaction_type,
                owner_ids=owner_ids,
                min_absolute_transaction_value_usd=min_absolute_transaction_value_usd,
                sort_by=sort_by,
                limit=limit,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in resolved.id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, CompanyInsiderTrades] = {}
    notes: list[str] = []
    for task in tasks:
        identifier = task.result_key
        if task.error:
            errors[identifier].append(task.error)
            continue
        resp: InsiderTradesResp = task.result
        errors[identifier].extend(resp.errors.values())
        trades_result = resp.results
        if trades_result.trades:
            results[identifier] = CompanyInsiderTrades(
                trades=trades_result.trades, total_matching=trades_result.total_matching
            )
            if trades_result.total_matching > len(trades_result.trades):
                notes.append(
                    truncation_note(
                        identifier,
                        len(trades_result.trades),
                        trades_result.total_matching,
                        "trades",
                    )
                )

    return GetInsiderTradesFromIdentifiersResp(
        identifier_results=results,
        identifier_errors=errors,
        identifier_info=resolved.id_triples,
        notes=notes or None,
    )


def api_limit(limit: int | None) -> int | str:
    """Convert a tool limit to the API's limit, where null means every match."""
    return "all" if limit is None else limit


async def fetch_owners_from_company_id(
    company_id: int,
    httpx_client: httpx2.AsyncClient,
    owner_type: OwnerTypeCategory = OwnerTypeCategory.all,
    position_changes: list[PositionChange] | None = None,
    owner_ids: list[int] | None = None,
    min_pct_shares_outstanding: float | None = None,
    funds_view: FundsView = FundsView.exclude_funds,
    sort_by: OwnersSortBy = OwnersSortBy.shares_held,
    limit: int | None = DEFAULT_LIMIT,
) -> OwnersResp:
    """Fetch owners for one company_id."""
    payload: dict[str, Any] = {
        "company_id": company_id,
        "funds_view": funds_view,
        "sort_by": sort_by,
        "limit": api_limit(limit),
    }
    if owner_type != OwnerTypeCategory.all:
        payload["owner_types"] = OWNER_TYPES_BY_CATEGORY[owner_type]
    if position_changes is not None:
        payload["position_changes"] = position_changes
    if owner_ids is not None:
        payload["owner_ids"] = owner_ids
    if min_pct_shares_outstanding is not None:
        payload["min_pct_shares_outstanding"] = min_pct_shares_outstanding

    resp = await httpx_client.post(url="/ownership/owners/", json=payload)
    resp.raise_for_status()
    return OwnersResp.model_validate(resp.json())


async def fetch_owners_summary_from_company_id(
    company_id: int,
    httpx_client: httpx2.AsyncClient,
) -> OwnersSummaryResp:
    """Fetch the ownership summary for one company_id."""
    resp = await httpx_client.post(
        url="/ownership/owners_summary/", json={"company_id": company_id}
    )
    resp.raise_for_status()
    return OwnersSummaryResp.model_validate(resp.json())


async def fetch_holdings_from_company_id(
    company_id: int,
    httpx_client: httpx2.AsyncClient,
    held_company_type: HeldCompanyTypeCategory = HeldCompanyTypeCategory.all,
    held_company_ids: list[int] | None = None,
    min_pct_portfolio: float | None = None,
    min_pct_shares_outstanding: float | None = None,
    limit: int | None = DEFAULT_LIMIT,
) -> HoldingsResp:
    """Fetch portfolio holdings for one owner company_id."""
    payload: dict[str, Any] = {"company_id": company_id, "limit": api_limit(limit)}
    if held_company_type != HeldCompanyTypeCategory.all:
        payload["held_company_types"] = HELD_COMPANY_TYPES_BY_CATEGORY[held_company_type]
    if held_company_ids is not None:
        payload["held_company_ids"] = held_company_ids
    if min_pct_portfolio is not None:
        payload["min_pct_portfolio"] = min_pct_portfolio
    if min_pct_shares_outstanding is not None:
        payload["min_pct_shares_outstanding"] = min_pct_shares_outstanding

    resp = await httpx_client.post(url="/ownership/holdings/", json=payload)
    resp.raise_for_status()
    return HoldingsResp.model_validate(resp.json())


async def fetch_insider_trades_from_company_id(
    company_id: int,
    httpx_client: httpx2.AsyncClient,
    start_date: date | None = None,
    end_date: date | None = None,
    transaction_type: InsiderTransactionCategory = InsiderTransactionCategory.all,
    owner_ids: list[int] | None = None,
    min_absolute_transaction_value_usd: float | None = None,
    sort_by: InsiderTradesSortBy = InsiderTradesSortBy.date,
    limit: int | None = DEFAULT_LIMIT,
) -> InsiderTradesResp:
    """Fetch insider trades for one company_id."""
    payload: dict[str, Any] = {
        "company_id": company_id,
        "sort_by": sort_by,
        "limit": api_limit(limit),
    }
    if start_date is not None:
        payload["start_date"] = start_date.isoformat()
    if end_date is not None:
        payload["end_date"] = end_date.isoformat()
    if transaction_type != InsiderTransactionCategory.all:
        payload["transaction_types"] = INSIDER_TRANSACTION_TYPES_BY_CATEGORY[transaction_type]
    if owner_ids is not None:
        payload["owner_ids"] = owner_ids
    if min_absolute_transaction_value_usd is not None:
        payload["min_absolute_transaction_value_usd"] = min_absolute_transaction_value_usd

    resp = await httpx_client.post(url="/ownership/insider_trades/", json=payload)
    resp.raise_for_status()
    return InsiderTradesResp.model_validate(resp.json())
