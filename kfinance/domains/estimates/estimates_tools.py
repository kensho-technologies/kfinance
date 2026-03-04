from abc import ABC, abstractmethod
from textwrap import dedent
from typing import Literal, Type

import httpx
from pydantic import BaseModel, Field

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.models.date_and_period_models import (
    EstimatePeriodType,
    EstimateType,
    NumPeriodsBackward,
    NumPeriodsForward,
)
from kfinance.client.permission_models import Permission
from kfinance.domains.estimates.estimates_models import EstimatesResp
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
    ValidQuarter,
)


class GetEstimatesFromIdentifiersArgs(ToolArgsWithIdentifiers):
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
        default=None, description="The number of periods forward from today (1-99)."
    )
    num_periods_backward: NumPeriodsBackward | None = Field(
        default=None,
        description="The number of periods to look back from today (1-99).",
    )


class GetEstimatesFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, EstimatesResp]  # identifier -> response


class GetEstimatesFromIdentifiers(KfinanceTool, ABC):
    args_schema: Type[BaseModel] = GetEstimatesFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.EstimatesPermission}

    @property
    @abstractmethod
    def estimate_type(self) -> EstimateType:
        """The estimate type property."""
        pass

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
    ) -> GetEstimatesFromIdentifiersResp:
        """"""
        return await get_estimates_from_identifiers(
            identifiers=identifiers,
            estimate_type=self.estimate_type,
            httpx_client=self.kfinance_client.httpx_client,
            period_type=period_type,
            fiscal_start_year=fiscal_start_year,
            fiscal_end_year=fiscal_end_year,
            fiscal_start_quarter=fiscal_start_quarter,
            fiscal_end_quarter=fiscal_end_quarter,
            num_periods_forward=num_periods_forward,
            num_periods_backward=num_periods_backward,
        )


class GetConsensusEstimatesFromIdentifiers(GetEstimatesFromIdentifiers):
    name: str = "get_consensus_estimates_from_identifiers"
    description: str = dedent("""
        Get consensus analyst estimates (EPS, Revenue, EBITDA, etc.) for a given company id. Returns statistical aggregates including high, low, mean, median, and number of estimates. When periods have ended, actual reported values are also returned.
    """).strip()

    @property
    def estimate_type(self) -> EstimateType:
        """The estimate type is consensus."""
        return EstimateType.consensus


class GetGuidanceFromIdentifiers(GetEstimatesFromIdentifiers):
    name: str = "get_guidance_from_identifiers"
    description: str = dedent("""
        Get company-issued financial guidance for a given company id. Returns the most recent guidance provided by the company for future periods, or the final guidance issued before results were reported for past periods.
    """).strip()

    @property
    def estimate_type(self) -> EstimateType:
        """The estimate type is guidance."""
        return EstimateType.guidance


async def get_estimates_from_identifiers(
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
) -> GetEstimatesFromIdentifiersResp:
    """Fetch estimates for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_estimates_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                estimate_type=estimate_type,
                httpx_client=httpx_client,
                period_type=period_type,
                fiscal_start_year=fiscal_start_year,
                fiscal_end_year=fiscal_end_year,
                fiscal_start_quarter=fiscal_start_quarter,
                fiscal_end_quarter=fiscal_end_quarter,
                num_periods_forward=num_periods_forward,
                num_periods_backward=num_periods_backward,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, EstimatesResp] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            results[task.result_key] = task.result

    return GetEstimatesFromIdentifiersResp(results=results, errors=errors)


async def fetch_estimates_from_company_id(
    company_id: int,
    estimate_type: EstimateType,
    httpx_client: httpx.AsyncClient,
    period_type: EstimatePeriodType | None = None,
    fiscal_start_year: int | None = None,
    fiscal_end_year: int | None = None,
    fiscal_start_quarter: Literal[1, 2, 3, 4] | None = None,
    fiscal_end_quarter: Literal[1, 2, 3, 4] | None = None,
    num_periods_forward: int | None = None,
    num_periods_backward: int | None = None,
) -> EstimatesResp:
    """Fetch estimates for one company_id."""
    # Build query parameters
    params = {
        "company_id": company_id,
        "estimate_type": estimate_type.value,
    }

    if period_type is not None:
        params["period_type"] = period_type.value
    if fiscal_start_year is not None:
        params["start_year"] = fiscal_start_year
    if fiscal_end_year is not None:
        params["end_year"] = fiscal_end_year
    if fiscal_start_quarter is not None:
        params["start_quarter"] = fiscal_start_quarter
    if fiscal_end_quarter is not None:
        params["end_quarter"] = fiscal_end_quarter
    if num_periods_forward is not None:
        params["num_periods_forward"] = num_periods_forward
    if num_periods_backward is not None:
        params["num_periods_backward"] = num_periods_backward

    resp = await httpx_client.post(url="/estimates/", json=params)
    response_data = resp.json()

    # Extract the result for this specific company_id
    company_result = response_data["results"][str(company_id)]
    return EstimatesResp.model_validate(company_result)
