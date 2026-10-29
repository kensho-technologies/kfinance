from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from textwrap import dedent
from typing import Any, Type

import httpx2
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.ownership.ownership_models import (
    CompanyOwners,
    Holding,
    Holdings,
    HoldingsResp,
    InsiderTrade,
    InsiderTrades,
    InsiderTradesResp,
    Owner,
    OwnersResp,
    OwnersSummaryResp,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithIdInfoAndErrors,
)


# The default number of owners or holdings returned per identifier, so that a widely held company
# or a large asset manager doesn't fill the context.
DEFAULT_OWNERS_AND_HOLDINGS_LIMIT = 300


class GetOwnersFromIdentifiersArgs(ToolArgsWithIdentifiers):
    min_pct_shares_outstanding: float | None = Field(
        default=None,
        description="Only return owners holding at least this percent of the company (e.g. 5 for 5%). Owners with a position are compared on its percent_shares_outstanding and dropped when it is null. Owners with only a relationship are compared on its estimated_percent_ownership and kept when it is null, unless exclude_unknown_pct is set. Use null for no threshold.",
    )
    exclude_unknown_pct: bool = Field(
        default=False,
        description="With min_pct_shares_outstanding, also drop owners whose percent of the company is unknown (relationships with a null estimated_percent_ownership). Has no effect without a threshold.",
    )
    include_summary: bool = Field(
        default=False,
        description="Also return the company's aggregate ownership summary (institutional ownership %, number of holders, buyers/sellers, and shares held by owner type).",
    )
    limit: int | None = Field(
        default=DEFAULT_OWNERS_AND_HOLDINGS_LIMIT,
        description=f"Limit to the top N owners (controlling owners first, then by shares held). Defaults to {DEFAULT_OWNERS_AND_HOLDINGS_LIMIT}. Use null for no limit.",
        ge=1,
    )


class GetOwnersFromIdentifiersResp(ToolRespWithIdInfoAndErrors[CompanyOwners]):
    # None rather than an empty list when no notes apply, so that the field is dropped from
    # tool output (serialized with exclude_none=True) like an empty `errors` list is.
    notes: list[str] | None = None


class GetOwnersFromIdentifiers(KfinanceTool):
    name: str = "get_owners_from_identifiers"
    description: str = dedent("""
        Get the owners of a list of companies: institutions and individuals with a position from public filings, plus current investors, parent companies, and fund investors from company relationships (which also cover private companies). Each owner includes the owner name and id, the institution type, and, when available:
        - position: shares held, percent of shares outstanding, the change in shares since the prior period, and the holding date.
        - relationship: the relationship type (e.g. "Current Investment", "Current Subsidiary/Operating Unit", "Current Fund Investor"), the estimated percent ownership, and whether the owner has a controlling interest.

        Owners are ordered with controlling owners (e.g. parent companies) first, then owners with a position by shares held (largest first), then owners with only a relationship by estimated percent ownership (largest first).

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - Pass a ticker as given. Otherwise pass the company's full name with its legal suffix (e.g. "Apple Inc." rather than "Apple").
        - When an owner has both, prefer position.percent_shares_outstanding over relationship.estimated_percent_ownership: the estimate isn't derived from share counts and can differ significantly.
        - Funds run by an investment manager are not listed separately; their shares are generally reported under the manager.
        - Set include_summary=True for aggregate ownership questions: institutional ownership percentage, number of institutional holders, number of buyers/sellers/new buyers/closed positions, shares bought/sold, or the breakdown of shares held by owner type (e.g. institutions, individuals/insiders, public and other).
        - Use limit to return only the top N owners, and min_pct_shares_outstanding to return only owners above a percent ownership threshold.
        - Many relationships have no estimated_percent_ownership, and min_pct_shares_outstanding keeps them by default. Set exclude_unknown_pct=True to return only owners known to be above the threshold.
        - Only the top 300 owners are returned by default. Set limit to null to look up a specific owner that may be outside the top 300.
        - To find what a company or fund owns (its portfolio), use get_holdings_from_identifiers instead.

        Examples:
        Query: "Who are the largest shareholders of Apple?"
        Function: get_owners_from_identifiers(identifiers=["Apple Inc."], limit=10)

        Query: "Which institutions own more than 5% of SPGI and MSFT?"
        Function: get_owners_from_identifiers(identifiers=["SPGI", "MSFT"], min_pct_shares_outstanding=5, exclude_unknown_pct=True)

        Query: "What percent of Tesla is owned by institutions?"
        Function: get_owners_from_identifiers(identifiers=["Tesla, Inc."], include_summary=True, limit=10)

        Query: "How much NVIDIA does BlackRock own?"
        Function: get_owners_from_identifiers(identifiers=["NVDA"], limit=25)

        Query: "Which of Microsoft's top 20 holders increased their positions?"
        Function: get_owners_from_identifiers(identifiers=["MSFT"], limit=20)

        Query: "Are institutions net buyers or net sellers of Amazon?"
        Function: get_owners_from_identifiers(identifiers=["AMZN"], include_summary=True, limit=10)

        Query: "Compare insider and institutional ownership of JPM, BAC, and WFC"
        Function: get_owners_from_identifiers(identifiers=["JPM", "BAC", "WFC"], include_summary=True, limit=5)
    """).strip()
    args_schema: Type[BaseModel] = GetOwnersFromIdentifiersArgs
    # TODO: switch to Permission.OwnershipPermission once the server's OwnershipPermission has product codes
    accepted_permissions: set[Permission] | None = {Permission.OnlyStaffPermission}

    async def _arun(
        self,
        identifiers: list[str],
        min_pct_shares_outstanding: float | None = None,
        exclude_unknown_pct: bool = False,
        include_summary: bool = False,
        limit: int | None = DEFAULT_OWNERS_AND_HOLDINGS_LIMIT,
    ) -> GetOwnersFromIdentifiersResp:
        """"""
        return await get_owners_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
            min_pct_shares_outstanding=min_pct_shares_outstanding,
            exclude_unknown_pct=exclude_unknown_pct,
            include_summary=include_summary,
            limit=limit,
        )


class GetHoldingsFromIdentifiersArgs(ToolArgsWithIdentifiers):
    min_pct_of_portfolio: float | None = Field(
        default=None,
        description="Only return holdings that make up at least this percent of the owner's portfolio (e.g. 5 for 5%), summed across the held company's securities. Holdings with no percent of portfolio are kept unless exclude_unknown_pct is set. Use null for no threshold.",
    )
    exclude_unknown_pct: bool = Field(
        default=False,
        description="With min_pct_of_portfolio, also drop holdings with no percent of portfolio. Has no effect without a threshold.",
    )
    limit: int | None = Field(
        default=DEFAULT_OWNERS_AND_HOLDINGS_LIMIT,
        description=f"Limit to the top N held companies (controlling interests first, then by percent of portfolio). Defaults to {DEFAULT_OWNERS_AND_HOLDINGS_LIMIT}. Use null for no limit.",
        ge=1,
    )


class GetHoldingsFromIdentifiersResp(ToolRespWithIdInfoAndErrors[Holdings]):
    pass


class GetHoldingsFromIdentifiers(KfinanceTool):
    name: str = "get_holdings_from_identifiers"
    description: str = dedent("""
        Get the holdings of a list of owners (e.g. asset managers, funds, or other companies): portfolio positions from public filings, plus current investments and fund investments from company relationships (which also cover stakes in private companies). The identifiers are the owners, not the companies being held. Each holding lists the held company and, when available:
        - positions: the owner's positions in the held company's securities, including ticker, shares held, percent of the owner's portfolio, percent of shares outstanding, and the holding date. Empty for holdings that only have a relationship.
        - relationship: the relationship type (e.g. "Current Investment", "Current Fund Investor"), the estimated percent ownership, and whether the owner has a controlling interest.

        Holdings are ordered with controlling interests first, then holdings with positions by percent of portfolio (largest first), then holdings with only a relationship by estimated percent ownership (largest first).

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - Pass a ticker as given. Otherwise pass the owner's full name with its legal suffix (e.g. "The Vanguard Group, Inc." rather than "Vanguard"). Short or informal names of asset managers can resolve to the wrong entity.
        - When a holding has both, prefer a position's percent_shares_outstanding over relationship.estimated_percent_ownership: the estimate isn't derived from share counts and can differ significantly.
        - Use limit to return only the top N held companies, and min_pct_of_portfolio to return only holdings above a percent of portfolio threshold.
        - Holdings with only a relationship have no percent of portfolio, and min_pct_of_portfolio keeps them by default. Set exclude_unknown_pct=True to return only holdings known to be above the threshold.
        - Only the top 300 held companies are returned by default. Set limit to null to check whether an owner holds a specific company that may be outside the top 300.
        - To find who owns a company, use get_owners_from_identifiers instead.

        Examples:
        Query: "What are Berkshire Hathaway's largest holdings?"
        Function: get_holdings_from_identifiers(identifiers=["Berkshire Hathaway Inc."], limit=10)

        Query: "Which companies does Vanguard hold?"
        Function: get_holdings_from_identifiers(identifiers=["The Vanguard Group, Inc."])

        Query: "What share of Berkshire Hathaway's portfolio is in Apple?"
        Function: get_holdings_from_identifiers(identifiers=["Berkshire Hathaway Inc."], limit=10)

        Query: "Which positions make up more than 5% of Pershing Square's portfolio?"
        Function: get_holdings_from_identifiers(identifiers=["Pershing Square Capital Management, L.P."], min_pct_of_portfolio=5, exclude_unknown_pct=True)

        Query: "Compare the top 5 holdings of BlackRock and Vanguard"
        Function: get_holdings_from_identifiers(identifiers=["BlackRock, Inc.", "The Vanguard Group, Inc."], limit=5)

        Query: "How concentrated is Pershing Square's portfolio?"
        Function: get_holdings_from_identifiers(identifiers=["Pershing Square Capital Management, L.P."])
    """).strip()
    args_schema: Type[BaseModel] = GetHoldingsFromIdentifiersArgs
    # TODO: switch to Permission.OwnershipPermission once the server's OwnershipPermission has product codes
    accepted_permissions: set[Permission] | None = {Permission.OnlyStaffPermission}

    async def _arun(
        self,
        identifiers: list[str],
        min_pct_of_portfolio: float | None = None,
        exclude_unknown_pct: bool = False,
        limit: int | None = DEFAULT_OWNERS_AND_HOLDINGS_LIMIT,
    ) -> GetHoldingsFromIdentifiersResp:
        """"""
        return await get_holdings_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
            min_pct_of_portfolio=min_pct_of_portfolio,
            exclude_unknown_pct=exclude_unknown_pct,
            limit=limit,
        )


# The limit applied when no date range is given, so that a company's full trade history doesn't
# fill the context. With a date range, all trades in it are returned.
DEFAULT_INSIDER_TRADES_LIMIT = 200


class GetInsiderTradesFromIdentifiersArgs(ToolArgsWithIdentifiers):
    start_date: date | None = Field(
        default=None,
        description="Filter trades to those made on or after this date (YYYY-MM-DD format)",
    )
    end_date: date | None = Field(
        default=None,
        description="Filter trades to those made on or before this date (YYYY-MM-DD format)",
    )
    limit: int | None = Field(
        default=None,
        description="Limit to the N most recent trades per company. Defaults to 200 when neither start_date nor end_date is set, and to no limit otherwise.",
        ge=1,
    )

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        """Reject a start_date after the end_date, which would match no trades."""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError(
                f"start_date ({self.start_date}) must be on or before end_date ({self.end_date})."
            )
        return self


class GetInsiderTradesFromIdentifiersResp(ToolRespWithIdInfoAndErrors[InsiderTrades]):
    pass


class GetInsiderTradesFromIdentifiers(KfinanceTool):
    name: str = "get_insider_trades_from_identifiers"
    description: str = dedent("""
        Get the insider trades (trades by officers, directors, and other insiders filed with the SEC) for a list of companies, most recent first. Each trade includes the insider name and id, transaction type, security type, number of shares, min and max price per share, transaction value in USD, trade date, and filing date.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - Pass a ticker as given. Otherwise pass the company's full name with its legal suffix (e.g. "NVIDIA Corporation" rather than "Nvidia").
        - shares is negative for dispositions (e.g. sales).
        - Use start_date and end_date to filter by trade date, and limit to return only the N most recent trades.
        - Without start_date or end_date, only the 200 most recent trades per company are returned. Set a date range for questions about a period (e.g. net buying or selling in a year) so no trades in it are cut off.

        Examples:
        Query: "Show me recent insider trades at Nvidia"
        Function: get_insider_trades_from_identifiers(identifiers=["NVIDIA Corporation"], limit=20)

        Query: "Did insiders at AAPL or MSFT sell stock in 2024?"
        Function: get_insider_trades_from_identifiers(identifiers=["AAPL", "MSFT"], start_date="2024-01-01", end_date="2024-12-31")

        Query: "What were the largest insider purchases at Meta since January 2025?"
        Function: get_insider_trades_from_identifiers(identifiers=["META"], start_date="2025-01-01")

        Query: "Were Tesla insiders net buyers or net sellers in 2025?"
        Function: get_insider_trades_from_identifiers(identifiers=["TSLA"], start_date="2025-01-01", end_date="2025-12-31")

        Query: "Did insider selling at Amazon increase from 2024 to 2025?"
        Function: get_insider_trades_from_identifiers(identifiers=["AMZN"], start_date="2024-01-01", end_date="2025-12-31")

        Query: "Show the 10 most recent insider trades at SPGI and MCO"
        Function: get_insider_trades_from_identifiers(identifiers=["SPGI", "MCO"], limit=10)
    """).strip()
    args_schema: Type[BaseModel] = GetInsiderTradesFromIdentifiersArgs
    # TODO: switch to Permission.OwnershipPermission once the server's OwnershipPermission has product codes
    accepted_permissions: set[Permission] | None = {Permission.OnlyStaffPermission}

    async def _arun(
        self,
        identifiers: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int | None = None,
    ) -> GetInsiderTradesFromIdentifiersResp:
        """"""
        return await get_insider_trades_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
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


def owners_notes(results: Iterable[CompanyOwners]) -> list[str]:
    """Return the notes that apply to the owners and ownership summaries being returned."""
    results = list(results)
    owners = [owner for result in results for owner in result.owners]
    summaries = [result.summary for result in results if result.summary is not None]

    notes: list[str] = []
    if any(
        owner.position is not None and owner.position.percent_shares_changed is None
        for owner in owners
    ):
        notes.append(FIRST_APPEARANCE_NOTE)
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


def owner_percent_ownership(owner: Owner) -> Decimal | None:
    """Return the owner's percent of the company, preferring its position over its relationship."""
    if owner.position is not None and owner.position.percent_shares_outstanding is not None:
        return owner.position.percent_shares_outstanding
    if owner.relationship is not None:
        return owner.relationship.estimated_percent_ownership
    return None


def filter_owners_by_min_pct(
    owners: list[Owner],
    min_pct_shares_outstanding: float | None,
    exclude_unknown_pct: bool = False,
) -> list[Owner]:
    """Drop owners known to hold less than min_pct_shares_outstanding percent of the company.

    The server applies the threshold to positions, dropping owners whose position has no percent
    of shares outstanding, but returns owners with only a relationship unfiltered. This applies it
    to their estimated percent ownership instead, and keeps the ones without an estimate unless
    exclude_unknown_pct is set.
    """
    if min_pct_shares_outstanding is None:
        return owners
    min_pct = Decimal(str(min_pct_shares_outstanding))
    filtered_owners: list[Owner] = []
    for owner in owners:
        percent = owner_percent_ownership(owner)
        if percent is None:
            if not exclude_unknown_pct:
                filtered_owners.append(owner)
        elif percent >= min_pct:
            filtered_owners.append(owner)
    return filtered_owners


async def get_owners_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx2.AsyncClient,
    min_pct_shares_outstanding: float | None = None,
    exclude_unknown_pct: bool = False,
    include_summary: bool = False,
    limit: int | None = DEFAULT_OWNERS_AND_HOLDINGS_LIMIT,
) -> GetOwnersFromIdentifiersResp:
    """Fetch owners (and optionally the ownership summary) for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    owners_tasks = [
        AsyncTask(
            func=fetch_owners_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                httpx_client=httpx_client,
                min_pct_shares_outstanding=min_pct_shares_outstanding,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]
    summary_tasks = (
        [
            AsyncTask(
                func=fetch_owners_summary_from_company_id,
                kwargs=dict(company_id=id_triple.company_id, httpx_client=httpx_client),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]
        if include_summary
        else []
    )

    await batch_execute_async_tasks(tasks=owners_tasks + summary_tasks)

    results: dict[str, CompanyOwners] = dict()
    for owners_task in owners_tasks:
        if owners_task.error:
            errors.append(owners_task.error)
            continue
        owners_resp: OwnersResp = owners_task.result
        errors.extend(f"{owners_task.result_key}: {error}" for error in owners_resp.errors.values())
        owners = filter_owners_by_min_pct(
            owners_resp.results.ownership, min_pct_shares_outstanding, exclude_unknown_pct
        )
        if owners:
            results[owners_task.result_key] = CompanyOwners(owners=owners[:limit])
        elif owners_resp.results.ownership:
            # Match the server's error when its own filter leaves no owners.
            errors.append(f"{owners_task.result_key}: No owners found.")

    for summary_task in summary_tasks:
        summary_errors: list[str] = []
        if summary_task.error:
            summary_errors.append(summary_task.error)
        else:
            summary_resp: OwnersSummaryResp = summary_task.result
            summary_errors.extend(
                f"{summary_task.result_key}: {error}" for error in summary_resp.errors.values()
            )
            if summary_resp.results is not None:
                results.setdefault(
                    summary_task.result_key, CompanyOwners()
                ).summary = summary_resp.results
        for error_msg in summary_errors:
            # Skip errors that the owners call already reported, like "Company not found." or a
            # request error that both calls hit.
            if error_msg not in errors:
                errors.append(error_msg)

    return GetOwnersFromIdentifiersResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        notes=owners_notes(results.values()) or None,
        errors=errors,
    )


def holding_percent_of_portfolio(holding: Holding) -> Decimal | None:
    """Return the percent of the owner's portfolio in the held company, summed across positions.

    Returns None when no position has a percent of portfolio.
    """
    percents = [
        position.percent_of_portfolio
        for position in holding.positions
        if position.percent_of_portfolio is not None
    ]
    return sum(percents, Decimal(0)) if percents else None


def filter_holdings_by_min_pct(
    holdings: list[Holding],
    min_pct_of_portfolio: float | None,
    exclude_unknown_pct: bool = False,
) -> list[Holding]:
    """Drop holdings known to make up less than min_pct_of_portfolio percent of the portfolio.

    Holdings without a percent of portfolio are kept unless exclude_unknown_pct is set.
    """
    if min_pct_of_portfolio is None:
        return holdings
    min_pct = Decimal(str(min_pct_of_portfolio))
    filtered_holdings: list[Holding] = []
    for holding in holdings:
        percent = holding_percent_of_portfolio(holding)
        if percent is None:
            if not exclude_unknown_pct:
                filtered_holdings.append(holding)
        elif percent >= min_pct:
            filtered_holdings.append(holding)
    return filtered_holdings


async def get_holdings_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx2.AsyncClient,
    min_pct_of_portfolio: float | None = None,
    exclude_unknown_pct: bool = False,
    limit: int | None = DEFAULT_OWNERS_AND_HOLDINGS_LIMIT,
) -> GetHoldingsFromIdentifiersResp:
    """Fetch portfolio holdings for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_holdings_from_company_id,
            kwargs=dict(company_id=id_triple.company_id, httpx_client=httpx_client),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, Holdings] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
            continue
        resp: HoldingsResp = task.result
        errors.extend(f"{task.result_key}: {error}" for error in resp.errors.values())
        holdings = filter_holdings_by_min_pct(
            resp.results.holdings, min_pct_of_portfolio, exclude_unknown_pct
        )
        if holdings:
            results[task.result_key] = Holdings(holdings=holdings[:limit])
        elif resp.results.holdings:
            # Match the server's error when it finds no holdings.
            errors.append(f"{task.result_key}: No holdings found.")

    return GetHoldingsFromIdentifiersResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
    )


def filter_insider_trades(
    trades: list[InsiderTrade],
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = None,
) -> list[InsiderTrade]:
    """Filter insider trades by trade date range and optionally limit results.

    Trades are expected to be ordered most recent first, so limit keeps the most recent trades.
    """
    if start_date or end_date:
        # Skip trades without a trade_date if filtering by date
        trades = [
            trade
            for trade in trades
            if trade.trade_date is not None
            and (start_date is None or trade.trade_date.date() >= start_date)
            and (end_date is None or trade.trade_date.date() <= end_date)
        ]
    return trades[:limit]


async def get_insider_trades_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx2.AsyncClient,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = None,
) -> GetInsiderTradesFromIdentifiersResp:
    """Fetch insider trades for all identifiers.

    Without a limit or date range, only the DEFAULT_INSIDER_TRADES_LIMIT most recent trades per
    company are returned.
    """
    if limit is None and start_date is None and end_date is None:
        limit = DEFAULT_INSIDER_TRADES_LIMIT

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_insider_trades_from_company_id,
            kwargs=dict(company_id=id_triple.company_id, httpx_client=httpx_client),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, InsiderTrades] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
            continue
        resp: InsiderTradesResp = task.result
        errors.extend(f"{task.result_key}: {error}" for error in resp.errors.values())
        if resp.results.trades:
            results[task.result_key] = InsiderTrades(
                trades=filter_insider_trades(
                    trades=resp.results.trades,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                )
            )

    return GetInsiderTradesFromIdentifiersResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
    )


async def fetch_owners_from_company_id(
    company_id: int,
    httpx_client: httpx2.AsyncClient,
    min_pct_shares_outstanding: float | None = None,
) -> OwnersResp:
    """Fetch owners for one company_id."""
    payload: dict[str, Any] = {"company_id": company_id}
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
) -> HoldingsResp:
    """Fetch portfolio holdings for one owner company_id."""
    resp = await httpx_client.post(url="/ownership/holdings/", json={"company_id": company_id})
    resp.raise_for_status()
    return HoldingsResp.model_validate(resp.json())


async def fetch_insider_trades_from_company_id(
    company_id: int,
    httpx_client: httpx2.AsyncClient,
) -> InsiderTradesResp:
    """Fetch insider trades for one company_id."""
    resp = await httpx_client.post(
        url="/ownership/insider_trades/", json={"company_id": company_id}
    )
    resp.raise_for_status()
    return InsiderTradesResp.model_validate(resp.json())
