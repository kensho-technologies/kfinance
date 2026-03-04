from datetime import date
from textwrap import dedent
from typing import Literal, Type

import httpx
from pydantic import BaseModel, Field

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.rounds_of_funding.rounds_of_funding_models import (
    AdvisorsResp,
    AdvisorTaskKey,
    FundingSummary,
    RoundOfFundingInfo,
    RoundOfFundingInfoWithAdvisors,
    RoundsOfFundingResp,
    RoundsOfFundingRole,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
)


class GetRoundsofFundingFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    role: RoundsOfFundingRole
    start_date: date | None = Field(
        default=None,
        description="Filter rounds to those closed on or after this date (YYYY-MM-DD format)",
    )
    end_date: date | None = Field(
        default=None,
        description="Filter rounds to those closed on or before this date (YYYY-MM-DD format)",
    )
    limit: int | None = Field(
        default=None, description="Limit to top N funding rounds by sort order"
    )
    sort_order: Literal["asc", "desc"] = Field(
        default="desc",
        description="Sort order for funding rounds by closed_date. 'desc' shows most recent first, 'asc' shows oldest first",
    )


class GetRoundsOfFundingFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, RoundsOfFundingResp]


def filter_rounds_of_funding_responses_by_date_range(
    rounds_of_funding_responses: dict[str, RoundsOfFundingResp],
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, RoundsOfFundingResp]:
    """Filter rounds of funding responses by date range"""
    if start_date or end_date:
        filtered_responses = {}
        for identifier, response in rounds_of_funding_responses.items():
            filtered_rounds = []
            for round_of_funding in response.rounds_of_funding:
                # Skip rounds without a closed_date if filtering by date
                if round_of_funding.closed_date is None:
                    continue

                if start_date and round_of_funding.closed_date < start_date:
                    continue
                if end_date and round_of_funding.closed_date > end_date:
                    continue

                filtered_rounds.append(round_of_funding)

            filtered_responses[identifier] = RoundsOfFundingResp(rounds_of_funding=filtered_rounds)

        return filtered_responses

    return rounds_of_funding_responses


def sort_and_limit_rounds_of_funding_responses(
    rounds_of_funding_responses: dict[str, RoundsOfFundingResp],
    sort_order: Literal["asc", "desc"] = "desc",
    limit: int | None = None,
) -> dict[str, RoundsOfFundingResp]:
    """Sort rounds of funding by closed_date and optionally limit results."""
    sorted_responses = {}
    for identifier, response in rounds_of_funding_responses.items():
        rounds = response.rounds_of_funding

        # Sort by closed_date (putting None dates at the end)
        if sort_order == "desc":
            rounds.sort(key=lambda r: r.closed_date or date.min, reverse=True)
        else:
            rounds.sort(key=lambda r: r.closed_date or date.max, reverse=False)

        if limit is not None:
            rounds = rounds[:limit]

        sorted_responses[identifier] = RoundsOfFundingResp(rounds_of_funding=rounds)
    return sorted_responses


class GetRoundsOfFundingFromIdentifiers(KfinanceTool):
    name: str = "get_rounds_of_funding_from_identifiers"
    description: str = dedent(f"""
        Returns funding round overviews: transaction_ids, types, dates, basic notes. Use for funding/capital raising questions (NOT M&A).

        ⚠️ TWO-STEP REQUIREMENT: Most questions need BOTH tools:
        1. Call THIS → get transaction_ids
        2. Call get_rounds_of_funding_info_from_transaction_ids with those IDs
        3. Answer using data from BOTH

        STEP 2 MANDATORY for: pricing trends (up/down-rounds), exact valuations, security details (preferred shares, classes, participation caps), advisors, board seats, liquidation terms, use of proceeds, pre-deal context, investor contribution amounts, transaction specifics (upsizing, textual notes), fees.

        ⚠️ Don't rely on funding_round_notes alone—it's unstructured/incomplete. Always call STEP 2 for detailed questions.

        ROLE PARAMETER:
        • '{RoundsOfFundingRole.company_raising_funds}': Company receiving funds (e.g., "What rounds did Stripe raise?")
        • '{RoundsOfFundingRole.company_investing_in_round_of_funding}': Investor's perspective (e.g., "Which companies did Sequoia invest in?")

        ⚠️ INVESTOR QUESTIONS: "How much did [INVESTOR] contribute to [COMPANY]'s round?" → Use INVESTOR's identifier with role=company_investing_in_round_of_funding
        Example: "How much did Blackbird VC contribute to Morse Micro's Series C?" → identifier=Blackbird VC, role=company_investing_in_round_of_funding
    """).strip()
    args_schema: Type[BaseModel] = GetRoundsofFundingFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}


    async def _arun(
        self,
        identifiers: list[str],
        role: RoundsOfFundingRole,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int | None = None,
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> GetRoundsOfFundingFromIdentifiersResp:
        """"""
        return await get_rounds_of_funding_from_identifiers(
            identifiers=identifiers,
            role=role,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            sort_order=sort_order,
            httpx_client=self.kfinance_client.httpx_client,
        )


class GetRoundsOfFundingInfoFromTransactionIdsArgs(BaseModel):
    transaction_ids: list[int] = Field(
        description="List of transaction IDs for rounds of funding.", min_length=1
    )


class GetRoundsOfFundingInfoFromTransactionIdsResp(ToolRespWithErrors):
    results: dict[int, RoundOfFundingInfoWithAdvisors]


def merge_round_of_info_reponses_with_advisors_responses(
    round_of_info_responses: dict[int, RoundOfFundingInfo],
    advisor_responses: dict[AdvisorTaskKey, AdvisorsResp],
) -> dict[int, RoundOfFundingInfoWithAdvisors]:
    """Merge round of info responses with advisors responses"""

    round_of_info_with_advisors = {}
    for transaction_id, round_of_info in round_of_info_responses.items():
        target_key = AdvisorTaskKey(
            transaction_id=transaction_id,
            role=RoundsOfFundingRole.company_raising_funds,
            company_id=round_of_info.participants.target.company_id,
        )
        target_advisors_resp = advisor_responses.get(target_key)
        target_advisors = target_advisors_resp.advisors if target_advisors_resp else []

        investor_advisors = {}
        for investor in round_of_info.participants.investors:
            investor_key = AdvisorTaskKey(
                transaction_id=transaction_id,
                role=RoundsOfFundingRole.company_investing_in_round_of_funding,
                company_id=investor.company_id,
            )
            advisor_resp = advisor_responses.get(investor_key)
            investor_advisors[investor.company_id] = advisor_resp.advisors if advisor_resp else []

        # Create round info with advisors
        round_of_info_with_advisors[transaction_id] = round_of_info.with_advisors(
            target_advisors=target_advisors, investor_advisors=investor_advisors
        )

    return round_of_info_with_advisors


class GetRoundsOfFundingInfoFromTransactionIds(KfinanceTool):
    name: str = "get_rounds_of_funding_info_from_transaction_ids"
    description: str = dedent("""
        Returns DETAILED transaction data. STEP 2 of the two-step workflow—call after get_rounds_of_funding_from_identifiers.

        Pass transaction_ids from STEP 1. Default: pass ALL IDs (efficient), then filter results. Only pass specific IDs if question names exact rounds (e.g., "Series A").

        Provides: advisors (legal, financial), board seats, governance rights, liquidation preferences/multiples, security terms (anti-dilution, participation caps, redemption), exact valuations (pre/post-money), use of proceeds, investor contribution amounts, transaction specifics (upsizing, textual notes), fees.

        MANDATORY for questions about: pricing trends (up/down-rounds), security details (preferred shares, classes), advisors, board seats, liquidation terms, exact valuations, use of proceeds, pre-deal context, investor contributions, transaction details (upsizing, notes), fees.

        Examples requiring this:
        • "What is the funding price trend for X—up or down-rounds?"
        • "Did X issue participating preferred shares with a cap?"
        • "How much did [investor] contribute to [company]'s Series C?"
        • "What was the post-money valuation for X's Series E?"
        • "Did X outline pre-deal operating context?"
    """).strip()
    args_schema: Type[BaseModel] = GetRoundsOfFundingInfoFromTransactionIdsArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}


    async def _arun(self, transaction_ids: list[int]) -> GetRoundsOfFundingInfoFromTransactionIdsResp:
        """"""
        return await get_rounds_of_funding_info_from_transaction_ids(
            transaction_ids=transaction_ids,
            httpx_client=self.kfinance_client.httpx_client,
        )


class GetFundingSummaryFromIdentifiersArgs(ToolArgsWithIdentifiers):
    pass  # Only needs identifiers, no additional args needed


class GetFundingSummaryFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, FundingSummary]


def build_funding_summaries_from_rof_responses(
    rounds_of_funding_responses: dict[str, RoundsOfFundingResp],
    detailed_round_info_responses: dict[int, RoundOfFundingInfo],
) -> dict[str, FundingSummary]:
    """Build funding summaries from rounds of funding and detailed round info responses."""
    summaries = {}
    for identifier, response in rounds_of_funding_responses.items():
        rounds = response.rounds_of_funding
        company_transaction_ids = [r.transaction_id for r in response.rounds_of_funding]

        total_rounds = len(rounds)
        dates = [r.closed_date for r in rounds if r.closed_date is not None]
        first_funding_date = min(dates) if dates else None
        most_recent_funding_date = max(dates) if dates else None

        rounds_by_type: dict[str, int] = {}
        for round_of_funding in rounds:
            funding_type = round_of_funding.funding_type or "Unknown"
            rounds_by_type[funding_type] = rounds_by_type.get(funding_type, 0) + 1

        total_capital_raised = None
        currency = None
        round_info_responses_with_aggregate_amount_raised = [
            detailed_round_info_responses[transaction_id]
            for transaction_id in company_transaction_ids
            if transaction_id in detailed_round_info_responses
            and detailed_round_info_responses[transaction_id].transaction.aggregate_amount_raised
            is not None
        ]
        # Sort transactions by closed_date descending to get most recent aggregate_amount_raised
        # (aggregate_amount_raised is cumulative, so the most recent round has the total)
        if round_info_responses_with_aggregate_amount_raised:
            if round_info_responses_with_aggregate_amount_raised:
                most_recent_round = max(
                    round_info_responses_with_aggregate_amount_raised,
                    key=lambda r: r.timeline.closed_date or date.min,
                )
                amount = most_recent_round.transaction.aggregate_amount_raised
                total_capital_raised = float(amount) if amount is not None else None
                currency = most_recent_round.transaction.currency

        summaries[identifier] = FundingSummary(
            company_id=identifier,
            total_capital_raised=total_capital_raised,
            total_capital_raised_currency=currency,
            total_rounds=total_rounds,
            first_funding_date=first_funding_date,
            most_recent_funding_date=most_recent_funding_date,
            rounds_by_type=rounds_by_type,
            sources=[
                {
                    "notes": "total_capital_raised, total_rounds, first_funding_date, most_recent_funding_date, and rounds_by_type are derived from underlying rounds of funding data that might be non-comprehensive."
                }
            ],
        )

    return summaries


class GetFundingSummaryFromIdentifiers(KfinanceTool):
    name: str = "get_funding_summary_from_identifiers"
    description: str = dedent("""
        Returns aggregate funding statistics: total_capital_raised, total_rounds count, first/most recent funding dates, rounds_by_type breakdown. No individual round details.

        ⚠️ Use for SIMPLE aggregates only (single summary numbers). For "CUMULATIVE" or "ACROSS ALL ROUNDS" questions, use get_rounds_of_funding_from_identifiers instead—those need individual rounds for verification/filtering.

        Use THIS for:
        • "How much TOTAL capital has X raised?" (if you don't need to verify individual rounds)
        • "How many rounds did X complete?"
        • "When was X's first/most recent funding?"

        DON'T use for:
        • "What is the cumulative amount raised by X across all disclosed rounds?" → Use get_rounds_of_funding_from_identifiers
        • "Show me X's funding history" → Use get_rounds_of_funding_from_identifiers
        • Any specific round questions → Use get_rounds_of_funding_from_identifiers

        ⚠️ If returns 0 rounds or null data, MUST follow up with get_rounds_of_funding_from_identifiers (summary often incomplete).
    """).strip()
    args_schema: Type[BaseModel] = GetFundingSummaryFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}


    async def _arun(self, identifiers: list[str]) -> GetFundingSummaryFromIdentifiersResp:
        """"""
        return await get_funding_summary_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def get_rounds_of_funding_from_identifiers(
    identifiers: list[str],
    role: RoundsOfFundingRole,
    httpx_client: httpx.AsyncClient,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = None,
    sort_order: Literal["asc", "desc"] = "desc",
) -> GetRoundsOfFundingFromIdentifiersResp:
    """Fetch rounds of funding for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_rounds_of_funding_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                role=role,
                httpx_client=httpx_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, RoundsOfFundingResp] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            results[task.result_key] = task.result

    filtered_responses = filter_rounds_of_funding_responses_by_date_range(
        results, start_date, end_date
    )

    sorted_responses = sort_and_limit_rounds_of_funding_responses(
        filtered_responses, sort_order, limit
    )

    return GetRoundsOfFundingFromIdentifiersResp(
        results=sorted_responses, errors=errors
    )


async def fetch_rounds_of_funding_from_company_id(
    company_id: int,
    role: RoundsOfFundingRole,
    httpx_client: httpx.AsyncClient,
) -> RoundsOfFundingResp:
    """Fetch rounds of funding for one company_id."""
    if role is RoundsOfFundingRole.company_raising_funds:
        url = f"/rounds_of_funding/{company_id}"
    else:
        url = f"/rounds_of_funding/investing_company/{company_id}"

    resp = await httpx_client.get(url=url)
    return RoundsOfFundingResp.model_validate(resp.json())


async def get_rounds_of_funding_info_from_transaction_ids(
    transaction_ids: list[int],
    httpx_client: httpx.AsyncClient,
) -> GetRoundsOfFundingInfoFromTransactionIdsResp:
    """Fetch detailed round of funding info for transaction IDs."""

    tasks = [
        AsyncTask(
            func=fetch_rounds_of_funding_info_from_transaction_id,
            kwargs=dict(
                transaction_id=transaction_id,
                httpx_client=httpx_client,
            ),
            result_key=transaction_id,
        )
        for transaction_id in transaction_ids
    ]

    await batch_execute_async_tasks(tasks=tasks)

    round_of_info_responses: dict[int, RoundOfFundingInfo] = dict()
    for task in tasks:
        if task.error:
            # For now, skip errors in individual round info fetches
            continue
        else:
            round_of_info_responses[task.result_key] = task.result

    # Fetch advisor info for all companies in all transactions
    advisor_tasks = []

    for transaction_id, round_of_info in round_of_info_responses.items():
        target_key = AdvisorTaskKey(
            transaction_id=transaction_id,
            role=RoundsOfFundingRole.company_raising_funds,
            company_id=round_of_info.participants.target.company_id,
        )
        advisor_tasks.append(
            AsyncTask(
                func=fetch_advisors_for_company_raising_round_of_funding,
                kwargs=dict(
                    transaction_id=transaction_id,
                    httpx_client=httpx_client,
                ),
                result_key=target_key,
            )
        )

        for investor in round_of_info.participants.investors:
            investor_key = AdvisorTaskKey(
                transaction_id=transaction_id,
                role=RoundsOfFundingRole.company_investing_in_round_of_funding,
                company_id=investor.company_id,
            )
            advisor_tasks.append(
                AsyncTask(
                    func=fetch_advisors_for_company_investing_in_round_of_funding,
                    kwargs=dict(
                        transaction_id=transaction_id,
                        advised_company_id=investor_key.company_id,
                        httpx_client=httpx_client,
                    ),
                    result_key=investor_key,
                )
            )

    await batch_execute_async_tasks(tasks=advisor_tasks)

    advisor_responses: dict[AdvisorTaskKey, AdvisorsResp] = dict()
    for task in advisor_tasks:
        if task.error:
            # Skip errors in advisor fetches
            continue
        else:
            advisor_responses[task.result_key] = task.result

    round_of_info_with_advisors = merge_round_of_info_reponses_with_advisors_responses(
        round_of_info_responses, advisor_responses
    )

    return GetRoundsOfFundingInfoFromTransactionIdsResp(
        results=round_of_info_with_advisors,
        errors=[],  # Individual API failures would be captured in batch execution
    )


async def fetch_rounds_of_funding_info_from_transaction_id(
    transaction_id: int,
    httpx_client: httpx.AsyncClient,
) -> RoundOfFundingInfo:
    """Fetch detailed round of funding info for one transaction_id."""
    url = f"/round_of_funding/info/{transaction_id}"
    resp = await httpx_client.get(url=url)
    return RoundOfFundingInfo.model_validate(resp.json())


async def fetch_advisors_for_company_raising_round_of_funding(
    transaction_id: int,
    httpx_client: httpx.AsyncClient,
) -> AdvisorsResp:
    """Fetch advisors for the target company raising funds in a round."""
    url = f"/round_of_funding/info/{transaction_id}/advisors/target"
    resp = await httpx_client.get(url=url)
    return AdvisorsResp.model_validate(resp.json())


async def fetch_advisors_for_company_investing_in_round_of_funding(
    transaction_id: int,
    advised_company_id: int,
    httpx_client: httpx.AsyncClient,
) -> AdvisorsResp:
    """Fetch advisors for an investing company in a round of funding."""
    url = f"/round_of_funding/info/{transaction_id}/advisors/investor/{advised_company_id}"
    resp = await httpx_client.get(url=url)
    return AdvisorsResp.model_validate(resp.json())


async def get_funding_summary_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
) -> GetFundingSummaryFromIdentifiersResp:
    """Fetch funding summaries for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_rounds_of_funding_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                role=RoundsOfFundingRole.company_raising_funds,
                httpx_client=httpx_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    rounds_of_funding_responses: dict[str, RoundsOfFundingResp] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            rounds_of_funding_responses[task.result_key] = task.result

    all_transaction_ids = []
    for response in rounds_of_funding_responses.values():
        transaction_ids = [r.transaction_id for r in response.rounds_of_funding]
        all_transaction_ids.extend(transaction_ids)

    detail_tasks = [
        AsyncTask(
            func=fetch_rounds_of_funding_info_from_transaction_id,
            kwargs=dict(
                transaction_id=transaction_id,
                httpx_client=httpx_client,
            ),
            result_key=transaction_id,
        )
        for transaction_id in all_transaction_ids
    ]

    await batch_execute_async_tasks(tasks=detail_tasks)

    detailed_round_info_responses: dict[int, RoundOfFundingInfo] = dict()
    for task in detail_tasks:
        if task.error:
            # Skip errors in individual detail fetches
            continue
        else:
            detailed_round_info_responses[task.result_key] = task.result

    summaries = build_funding_summaries_from_rof_responses(
        rounds_of_funding_responses, detailed_round_info_responses
    )

    return GetFundingSummaryFromIdentifiersResp(
        results=summaries, errors=errors
    )
