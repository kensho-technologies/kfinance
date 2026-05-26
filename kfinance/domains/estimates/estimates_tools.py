from datetime import date
from decimal import Decimal
from textwrap import dedent
from typing import Any, Literal, Type

import httpx
from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.models.date_and_period_models import (
    EstimatePeriodType,
    EstimateType,
    NumPeriodsBackward,
    NumPeriodsForward,
)
from kfinance.client.models.response_models import SingleResultResp
from kfinance.client.permission_models import Permission
from kfinance.domains.estimates.estimates_models import (
    AnalystRecommendations,
    ConsensusTargetPrice,
)
from kfinance.domains.line_items.line_item_models import CalendarType
from kfinance.domains.line_items.response_notes import insert_fiscal_period_notes
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithIdInfoAndErrors,
    ValidQuarter,
)
from pydantic import BaseModel, Field

from kfinance.domains.line_items.line_item_tools import AlternativeLineItemMetadata


class EstimateLineItem(BaseModel):
    name: str
    value: Decimal | None


class EstimatesPeriodData(BaseModel):
    period_end_date: date | None = None
    estimates: list[EstimateLineItem]


class Estimates(BaseModel):
    estimate_type: str
    currency: str | None
    period_type: str
    periods: dict[str, EstimatesPeriodData]


class GetEstimatesFromIdentifiersVaArgs(ToolArgsWithIdentifiers):
    period_type: EstimatePeriodType | None = Field(
        default=None, description="The period type (annual, semi-annual, or quarterly)."
    )
    fiscal_start_year: int | None = Field(
        default=None,
        description="The starting year for the data range. Use null for the most recent data.",
    )
    fiscal_end_year: int | None = Field(
        default=None,
        description="The ending year for the data range. Use null for the most recent data.",
    )
    fiscal_start_quarter: ValidQuarter | None = Field(
        default=None,
        description="Starting quarter (1-4). Used when period_type is semi-annual or quarterly.",
    )
    fiscal_end_quarter: ValidQuarter | None = Field(
        default=None,
        description="Ending quarter (1-4). Used when period_type is semi-annual or quarterly.",
    )
    num_periods_forward: NumPeriodsForward | None = Field(
        default=None, description="The number of periods forward from today (0-99)."
    )
    num_periods_backward: NumPeriodsBackward | None = Field(
        default=None,
        description="The number of periods to look back from today (0-99).",
    )
    estimate_search: str | None = Field(
        default=None,
        description="Freeform descriptive phrase for the estimate. Matched semantically.",
    )


class GetEstimatesFromIdentifiersVaResp(ToolRespWithIdInfoAndErrors[Estimates]):
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, AlternativeLineItemMetadata] = Field(default_factory=dict)


class PostResponseWithMetadata(BaseModel):
    results: dict[str, Estimates]
    errors: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, AlternativeLineItemMetadata] = Field(default_factory=dict)


async def fetch_estimates_from_company_ids_va(
    company_ids: list[int],
    estimate_type: EstimateType,
    httpx_client: httpx.AsyncClient,
    period_type: EstimatePeriodType | None = None,
    fiscal_start_year: int | None = None,
    fiscal_end_year: int | None = None,
    fiscal_start_quarter: Literal[1, 2, 3, 4] | None = None,
    fiscal_end_quarter: Literal[1, 2, 3, 4] | None = None,
    num_periods_forward: int | None = None,
    num_periods_backward: int | None = None,
    estimate_search: str | None = None,
) -> PostResponseWithMetadata:
    """Fetch estimates for a list of company IDs using Visible Alpha as the data source."""
    payload: dict[str, Any] = {
        "company_ids": company_ids,
        "estimate_type": estimate_type.value,
        "data_source_type": "visible_alpha",
    }

    if period_type is not None:
        payload["period_type"] = period_type.value
    if fiscal_start_year is not None:
        payload["start_year"] = fiscal_start_year
    if fiscal_end_year is not None:
        payload["end_year"] = fiscal_end_year
    if fiscal_start_quarter is not None:
        payload["start_quarter"] = fiscal_start_quarter
    if fiscal_end_quarter is not None:
        payload["end_quarter"] = fiscal_end_quarter
    if num_periods_forward is not None:
        payload["num_periods_forward"] = num_periods_forward
    if num_periods_backward is not None:
        payload["num_periods_backward"] = num_periods_backward
    if estimate_search is not None:
        payload["estimate_search"] = estimate_search

    resp = await httpx_client.post(url="/estimates/", json=payload)
    resp.raise_for_status()

    return PostResponseWithMetadata.model_validate(resp.json())


async def get_estimates_from_identifiers_va(
    identifiers: list[str],
    estimate_type: EstimateType,
    httpx_client: httpx.AsyncClient,
    period_type: EstimatePeriodType | None = None,
    fiscal_start_year: int | None = None,
    fiscal_end_year: int | None = None,
    fiscal_start_quarter: Literal[1, 2, 3, 4] | None = None,
    fiscal_end_quarter: Literal[1, 2, 3, 4] | None = None,
    num_periods_forward: int | None = None,
    num_periods_backward: int | None = None,
    estimate_search: str | None = None,
) -> GetEstimatesFromIdentifiersVaResp:
    """Fetch estimates for all identifiers using Visible Alpha as the data source."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    metadata: dict[str, AlternativeLineItemMetadata] = {}
    if id_triple_resp.company_ids:
        estimates_resp = await fetch_estimates_from_company_ids_va(
            company_ids=id_triple_resp.company_ids,
            estimate_type=estimate_type,
            httpx_client=httpx_client,
            period_type=period_type,
            fiscal_start_year=fiscal_start_year,
            fiscal_end_year=fiscal_end_year,
            fiscal_start_quarter=fiscal_start_quarter,
            fiscal_end_quarter=fiscal_end_quarter,
            num_periods_forward=num_periods_forward,
            num_periods_backward=num_periods_backward,
            estimate_search=estimate_search,
        )

        for company_id_str, error in estimates_resp.errors.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            errors.append(f"{original_identifier}: {error}")

        identifier_to_results = {}
        for company_id_str, estimates_data in estimates_resp.results.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            identifier_to_results[original_identifier] = estimates_data

        for company_id_str, meta in estimates_resp.metadata.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            metadata[original_identifier] = meta

        results = identifier_to_results
    else:
        results = {}

    resp_model = GetEstimatesFromIdentifiersVaResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
        metadata=metadata,
    )

    insert_fiscal_period_notes(
        calendar_type=CalendarType.fiscal,
        period_type=period_type,
        resp_model=resp_model,
    )

    if metadata:
        resp_model.notes.append(
            "If an alternative better matches your intent,"
            " call the tool again with that name as the estimate_search parameter."
        )

    return resp_model


class GetConsensusEstimatesFromIdentifiersVa(KfinanceTool):
    name: str = "get_consensus_estimates_from_identifiers"
    description: str = dedent("""
        Get consensus analyst estimates for a list of identifiers.

        Returns statistical aggregates including high, low, mean, median, and number of estimates. When periods have ended, actual reported values are also returned.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - To fetch the most recent estimates, leave all time parameters as null.
        - To filter by time, use either absolute time (fiscal_start_year, fiscal_end_year, fiscal_start_quarter, fiscal_end_quarter) OR relative time (num_periods_forward, num_periods_backward)—but not both.

        Examples:
        Query: "Get consensus EPS estimates for AAPL"
        Function: get_consensus_estimates_from_identifiers(identifiers=["AAPL"], estimate_search="EPS")

        Query: "Consensus iPhone unit sales for Apple for the next 4 quarters"
        Function: get_consensus_estimates_from_identifiers(identifiers=["AAPL"], estimate_search="iPhone unit sales", period_type="quarterly", num_periods_forward=4)

        Query: "Get annual consensus revenue estimates for SPGI for fiscal year 2024"
        Function: get_consensus_estimates_from_identifiers(identifiers=["SPGI"], estimate_search="revenue", period_type="annual", fiscal_start_year=2024, fiscal_end_year=2024)
    """).strip()
    args_schema: Type[BaseModel] = GetEstimatesFromIdentifiersVaArgs
    accepted_permissions: set[Permission] | None = {Permission.EstimatesPermission}

    async def _arun(
        self,
        identifiers: list[str],
        period_type: EstimatePeriodType | None = None,
        fiscal_start_year: int | None = None,
        fiscal_end_year: int | None = None,
        fiscal_start_quarter: Literal[1, 2, 3, 4] | None = None,
        fiscal_end_quarter: Literal[1, 2, 3, 4] | None = None,
        num_periods_forward: int | None = None,
        num_periods_backward: int | None = None,
        estimate_search: str | None = None,
    ) -> GetEstimatesFromIdentifiersVaResp:
        """"""
        return await get_estimates_from_identifiers_va(
            identifiers=identifiers,
            estimate_type=EstimateType.consensus,
            httpx_client=self.kfinance_client.httpx_client,
            period_type=period_type,
            fiscal_start_year=fiscal_start_year,
            fiscal_end_year=fiscal_end_year,
            fiscal_start_quarter=fiscal_start_quarter,
            fiscal_end_quarter=fiscal_end_quarter,
            num_periods_forward=num_periods_forward,
            num_periods_backward=num_periods_backward,
            estimate_search=estimate_search,
        )


# Alias for backwards compatibility with tool registries that import the
# non-VA name. The VA-backed implementation is the consensus tool.
GetConsensusEstimatesFromIdentifiers = GetConsensusEstimatesFromIdentifiersVa


class GetGuidanceFromIdentifiers(KfinanceTool):
    name: str = "get_guidance_from_identifiers"
    description: str = dedent("""
        Get company-issued financial guidance for a given identifier.

        Returns the most recent guidance provided by the company for future periods, or the final guidance issued before results were reported for past periods.
    """).strip()
    args_schema: Type[BaseModel] = GetEstimatesFromIdentifiersVaArgs
    accepted_permissions: set[Permission] | None = {Permission.EstimatesPermission}

    async def _arun(
        self,
        identifiers: list[str],
        period_type: EstimatePeriodType | None = None,
        fiscal_start_year: int | None = None,
        fiscal_end_year: int | None = None,
        fiscal_start_quarter: Literal[1, 2, 3, 4] | None = None,
        fiscal_end_quarter: Literal[1, 2, 3, 4] | None = None,
        num_periods_forward: int | None = None,
        num_periods_backward: int | None = None,
        estimate_search: str | None = None,
    ) -> GetEstimatesFromIdentifiersVaResp:
        """"""
        return await get_estimates_from_identifiers_va(
            identifiers=identifiers,
            estimate_type=EstimateType.guidance,
            httpx_client=self.kfinance_client.httpx_client,
            period_type=period_type,
            fiscal_start_year=fiscal_start_year,
            fiscal_end_year=fiscal_end_year,
            fiscal_start_quarter=fiscal_start_quarter,
            fiscal_end_quarter=fiscal_end_quarter,
            num_periods_forward=num_periods_forward,
            num_periods_backward=num_periods_backward,
            estimate_search=estimate_search,
        )


class GetConsensusTargetPriceFromIdentifiersResp(ToolRespWithIdInfoAndErrors[ConsensusTargetPrice]):
    pass


class GetConsensusTargetPriceFromIdentifiers(KfinanceTool):
    name: str = "get_consensus_target_price_from_identifiers"
    description: str = dedent("""
        Get consensus target price estimates for a given company. Returns the current consensus analyst target price including high, low, mean, and median values.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.EstimatesPermission}

    async def _arun(
        self,
        identifiers: list[str],
    ) -> GetConsensusTargetPriceFromIdentifiersResp:
        return await get_consensus_target_price_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
        )


class GetAnalystRecommendationsFromIdentifiersResp(
    ToolRespWithIdInfoAndErrors[AnalystRecommendations]
):
    pass


class GetAnalystRecommendationsFromIdentifiers(KfinanceTool):
    name: str = "get_analyst_recommendations_from_identifiers"
    description: str = dedent("""
        Get analyst recommendations for a given company. Returns the current consensus analyst recommendation breakdown including buy, hold, sell counts and overall rating.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.EstimatesPermission}

    async def _arun(
        self,
        identifiers: list[str],
    ) -> GetAnalystRecommendationsFromIdentifiersResp:
        return await get_analyst_recommendations_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def get_consensus_target_price_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
) -> GetConsensusTargetPriceFromIdentifiersResp:
    """Fetch consensus target price for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_consensus_target_price_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                httpx_client=httpx_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, ConsensusTargetPrice] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            resp: SingleResultResp[ConsensusTargetPrice] = task.result
            if resp.result is not None:
                results[task.result_key] = resp.result
            if resp.error is not None:
                error_msg = f"{task.result_key}: {resp.error}"
                errors.append(error_msg)

    return GetConsensusTargetPriceFromIdentifiersResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
    )


async def fetch_consensus_target_price_from_company_id(
    company_id: int,
    httpx_client: httpx.AsyncClient,
) -> SingleResultResp[ConsensusTargetPrice]:
    """Fetch consensus target price for one company_id."""
    resp = await httpx_client.get(url=f"/estimates/consensus_target_price/{company_id}")
    resp.raise_for_status()
    return SingleResultResp[ConsensusTargetPrice].model_validate(resp.json())


async def get_analyst_recommendations_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
) -> GetAnalystRecommendationsFromIdentifiersResp:
    """Fetch analyst recommendations for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_analyst_recommendations_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                httpx_client=httpx_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, AnalystRecommendations] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            resp: SingleResultResp[AnalystRecommendations] = task.result
            if resp.result is not None:
                results[task.result_key] = resp.result
            if resp.error is not None:
                error_msg = f"{task.result_key}: {resp.error}"
                errors.append(error_msg)

    return GetAnalystRecommendationsFromIdentifiersResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
    )


async def fetch_analyst_recommendations_from_company_id(
    company_id: int,
    httpx_client: httpx.AsyncClient,
) -> SingleResultResp[AnalystRecommendations]:
    """Fetch analyst recommendations for one company_id."""
    resp = await httpx_client.get(url=f"/estimates/analyst_recommendations/{company_id}")
    resp.raise_for_status()
    return SingleResultResp[AnalystRecommendations].model_validate(resp.json())
