from textwrap import dedent
from typing import Any, Literal, Type

import httpx
from pydantic import BaseModel, Field

from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.models.date_and_period_models import (
    EstimatePeriodType,
    EstimateType,
    NumPeriodsBackward,
    NumPeriodsForward,
)
from kfinance.client.permission_models import Permission
from kfinance.domains.estimates.estimates_models import Estimates
from kfinance.domains.line_items.line_item_models import AlternativeLineItemMetadata, CalendarType
from kfinance.domains.line_items.response_notes import insert_fiscal_period_notes
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithIdInfoAndErrors,
    ValidQuarter,
)


class GetVisibleAlphaEstimatesFromIdentifiersArgs(ToolArgsWithIdentifiers):
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
        description="The financial metric, business measure, or quantitative data point to retrieve. Use descriptive natural language. Preserve the specificity of what the user asked for; keep any product, model, series, segment, or region qualifiers they named rather than generalizing to a broader metric. When the user names several distinct items, make a separate call per item using its specific name.",
    )
    currency: str | None = Field(
        default=None,
        description="ISO 4217 currency code to return values in (e.g. 'USD', 'EUR'). Defaults to the reporting currency if not specified.",
    )


class PostResponseWithMetadata(BaseModel):
    results: dict[str, Estimates]
    errors: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, AlternativeLineItemMetadata] = Field(default_factory=dict)
    data_source: str | None = None


class GetVisibleAlphaEstimatesFromIdentifiersResp(ToolRespWithIdInfoAndErrors[Estimates]):
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, AlternativeLineItemMetadata] = Field(default_factory=dict)
    data_source: str = "Visible Alpha"


class GetVisibleAlphaConsensusEstimatesFromIdentifiers(KfinanceTool):
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
    args_schema: Type[BaseModel] = GetVisibleAlphaEstimatesFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.VisibleAlphaPermission}

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
        currency: str | None = None,
    ) -> GetVisibleAlphaEstimatesFromIdentifiersResp:
        """"""
        return await get_visible_alpha_estimates_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
            period_type=period_type,
            fiscal_start_year=fiscal_start_year,
            fiscal_end_year=fiscal_end_year,
            fiscal_start_quarter=fiscal_start_quarter,
            fiscal_end_quarter=fiscal_end_quarter,
            num_periods_forward=num_periods_forward,
            num_periods_backward=num_periods_backward,
            estimate_search=estimate_search,
            currency=currency,
        )


async def fetch_visible_alpha_estimates_from_company_ids(
    company_ids: list[int],
    httpx_client: httpx.AsyncClient,
    period_type: EstimatePeriodType | None = None,
    fiscal_start_year: int | None = None,
    fiscal_end_year: int | None = None,
    fiscal_start_quarter: Literal[1, 2, 3, 4] | None = None,
    fiscal_end_quarter: Literal[1, 2, 3, 4] | None = None,
    num_periods_forward: int | None = None,
    num_periods_backward: int | None = None,
    estimate_search: str | None = None,
    currency: str | None = None,
) -> PostResponseWithMetadata:
    """Fetch consensus estimates for a list of company IDs using Visible Alpha as the data source."""
    payload: dict[str, Any] = {
        "company_ids": company_ids,
        "estimate_type": EstimateType.consensus.value,
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
    if currency is not None:
        payload["currency"] = currency

    resp = await httpx_client.post(url="/estimates/visible_alpha", json=payload)
    resp.raise_for_status()

    return PostResponseWithMetadata.model_validate(resp.json())


async def get_visible_alpha_estimates_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
    period_type: EstimatePeriodType | None = None,
    fiscal_start_year: int | None = None,
    fiscal_end_year: int | None = None,
    fiscal_start_quarter: Literal[1, 2, 3, 4] | None = None,
    fiscal_end_quarter: Literal[1, 2, 3, 4] | None = None,
    num_periods_forward: int | None = None,
    num_periods_backward: int | None = None,
    estimate_search: str | None = None,
    currency: str | None = None,
) -> GetVisibleAlphaEstimatesFromIdentifiersResp:
    """Fetch estimates for all identifiers using Visible Alpha as the data source."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    metadata: dict[str, AlternativeLineItemMetadata] = {}
    if id_triple_resp.company_ids:
        estimates_resp = await fetch_visible_alpha_estimates_from_company_ids(
            company_ids=id_triple_resp.company_ids,
            httpx_client=httpx_client,
            period_type=period_type,
            fiscal_start_year=fiscal_start_year,
            fiscal_end_year=fiscal_end_year,
            fiscal_start_quarter=fiscal_start_quarter,
            fiscal_end_quarter=fiscal_end_quarter,
            num_periods_forward=num_periods_forward,
            num_periods_backward=num_periods_backward,
            estimate_search=estimate_search,
            currency=currency,
        )

        for company_id_str, error in estimates_resp.errors.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            errors.append(f"{original_identifier}: {error}")

        identifier_to_results = {}
        for company_id_str, estimates_data in estimates_resp.results.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            estimates_data.data_source = "Visible Alpha"
            identifier_to_results[original_identifier] = estimates_data

        for company_id_str, meta in estimates_resp.metadata.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            metadata[original_identifier] = meta

        results = identifier_to_results
    else:
        results = {}

    resp_model = GetVisibleAlphaEstimatesFromIdentifiersResp(
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
            "The result may not be an exact match. ALWAYS compare the returned"
            " estimate name against your intent and the listed"
            " `top_ranked_alternatives`. If any alternative is a closer match to"
            " what was asked, you MUST call the tool again using that exact"
            " alternative name as the `estimate_search` parameter before answering."
        )

    return resp_model
