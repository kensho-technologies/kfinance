from abc import ABC, abstractmethod
from textwrap import dedent
from typing import Any, Literal, Type, cast

import httpx2
from pydantic import BaseModel, Field, model_validator

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.models.date_and_period_models import (
    EstimatePeriodType,
    EstimateType,
    NumPeriodsBackward,
    NumPeriodsForward,
)
from kfinance.client.models.response_models import (
    PostResponseWithLineItemMetadata,
    SingleResultResp,
)
from kfinance.client.permission_models import Permission
from kfinance.domains.estimates.estimates_models import (
    CONSENSUS_LINE_ITEM_NAMES_AND_ALIASES,
    CONSENSUS_LINE_ITEM_TO_DESCRIPTIONS_MAP,
    GUIDANCE_LINE_ITEM_NAMES_AND_ALIASES,
    GUIDANCE_LINE_ITEM_TO_DESCRIPTIONS_MAP,
    AnalystRecommendations,
    CiqEstimates,
    ConsensusTargetPrice,
)
from kfinance.domains.line_items.line_item_models import AlternativeLineItemMetadata, CalendarType
from kfinance.domains.line_items.line_item_tools import smart_line_item_validator
from kfinance.domains.line_items.response_notes import (
    insert_fiscal_period_notes,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithIdInfoAndErrors,
    ValidQuarter,
)


class BaseEstimatesFromIdentifiersArgs(ToolArgsWithIdentifiers):
    period_type: EstimatePeriodType | None = Field(
        default=None, description="The period type (annual, semi-annual, or quarterly)."
    )
    num_periods_forward: NumPeriodsForward | None = Field(
        default=None, description="The number of periods forward from today (0-99)."
    )
    num_periods_backward: NumPeriodsBackward | None = Field(
        default=None,
        description="The number of periods to look back from today (0-99).",
    )


class GetEstimatesFromIdentifiersArgs(BaseEstimatesFromIdentifiersArgs):
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


class GetConsensusEstimatesFromIdentifiersArgs(GetEstimatesFromIdentifiersArgs):
    line_item: Literal[tuple(CONSENSUS_LINE_ITEM_NAMES_AND_ALIASES)] = Field(  # type: ignore[valid-type]
        description="The type of consensus estimate line_item requested"
    )

    @model_validator(mode="before")
    @classmethod
    def validate_line_item_with_suggestions(cls, values: dict) -> dict:
        """Custom validator that provides intelligent suggestions for invalid line items."""
        if isinstance(values, dict) and "line_item" in values:
            line_item = values["line_item"]
            if isinstance(line_item, list):
                raise ValueError(
                    "line_item takes one line item per call. Call this tool once per line item."
                )
            if not isinstance(line_item, str):
                raise ValueError(f"line_item must be a string, got {type(line_item).__name__}")
            # Use the helper function to validate and provide suggestions
            smart_line_item_validator(
                v=line_item,
                names_and_aliases=CONSENSUS_LINE_ITEM_NAMES_AND_ALIASES,
                items_to_descriptions=CONSENSUS_LINE_ITEM_TO_DESCRIPTIONS_MAP,
            )
        return values


class GetGuidanceEstimatesFromIdentifiersArgs(GetEstimatesFromIdentifiersArgs):
    line_item: Literal[tuple(GUIDANCE_LINE_ITEM_NAMES_AND_ALIASES)] = Field(  # type: ignore[valid-type]
        description="The type of guidance estimate line_item requested"
    )

    @model_validator(mode="before")
    @classmethod
    def validate_line_item_with_suggestions(cls, values: dict) -> dict:
        """Custom validator that provides intelligent suggestions for invalid line items."""
        if isinstance(values, dict) and "line_item" in values:
            line_item = values["line_item"]
            if isinstance(line_item, list):
                raise ValueError(
                    "line_item takes one line item per call. Call this tool once per line item."
                )
            if not isinstance(line_item, str):
                raise ValueError(f"line_item must be a string, got {type(line_item).__name__}")
            # Use the helper function to validate and provide suggestions
            smart_line_item_validator(
                v=line_item,
                names_and_aliases=GUIDANCE_LINE_ITEM_NAMES_AND_ALIASES,
                items_to_descriptions=GUIDANCE_LINE_ITEM_TO_DESCRIPTIONS_MAP,
            )
        return values


class GetCiqEstimatesFromIdentifiersResp(ToolRespWithIdInfoAndErrors[CiqEstimates]):
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, AlternativeLineItemMetadata] = Field(default_factory=dict)
    data_source: str


class GetEstimatesFromIdentifiers(KfinanceTool, ABC):
    accepted_permissions: set[Permission] | None = {Permission.EstimatesPermission}

    @property
    @abstractmethod
    def estimate_type(self) -> EstimateType:
        """The estimate type property."""
        pass

    async def _arun(
        self,
        identifiers: list[str],
        line_item: str,
        period_type: EstimatePeriodType | None = None,
        fiscal_start_year: int | None = None,
        fiscal_end_year: int | None = None,
        fiscal_start_quarter: Literal["1", "2", "3", "4"] | None = None,
        fiscal_end_quarter: Literal["1", "2", "3", "4"] | None = None,
        num_periods_forward: int | None = None,
        num_periods_backward: int | None = None,
    ) -> GetCiqEstimatesFromIdentifiersResp:
        """"""
        return await get_estimates_from_identifiers(
            identifiers=identifiers,
            line_item=line_item,
            estimate_type=self.estimate_type,
            httpx_client=self.kfinance_client.httpx_client,
            period_type=period_type,
            fiscal_start_year=fiscal_start_year,
            fiscal_end_year=fiscal_end_year,
            fiscal_start_quarter=cast(Literal[1, 2, 3, 4], int(fiscal_start_quarter))
            if fiscal_start_quarter
            else None,
            fiscal_end_quarter=cast(Literal[1, 2, 3, 4], int(fiscal_end_quarter))
            if fiscal_end_quarter
            else None,
            num_periods_forward=num_periods_forward,
            num_periods_backward=num_periods_backward,
        )


class GetConsensusEstimatesFromIdentifiers(GetEstimatesFromIdentifiers):
    name: str = "get_consensus_estimates_from_identifiers"
    description: str = dedent("""
        Get a single consensus analyst estimate (EPS, Revenue, EBITDA, etc.) for a list of identifiers. Returns Capital IQ data.
        Returns statistical aggregates including high, low, mean, median, and number of estimates. When periods have ended, actual reported values are also returned with "Actual" in the name.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - If no time parameters are provided, next 4 quarters are retrieved by default.
        - To filter by time, use either absolute time (start_year, end_year, start_quarter, end_quarter) OR relative time (num_periods_forward, num_periods_backward)—but not both.
        - 'EPS' by itself usually means 'normalized EPS', but it could also mean 'generally accepted accounting principles EPS' or 'EPS excluding exceptional items and goodwill'.

        Examples:
        Query: "EBITDA consensus estimates for Apple using Capital IQ data."
        Function: get_consensus_estimates_from_identifiers(identifiers=["AAPL"], line_item="ebitda")

        Query: "SAP consensus revenue estimates for fiscal 2027 through 2029 using Capital IQ data."
        Function: get_consensus_estimates_from_identifiers(identifiers=["SAP"], line_item="revenue", period_type="annual", start_year=2027, end_year=2029)

        Query: "Apple consensus EPS estimates for the most recently announced quarter using Capital IQ data."
        Function: get_consensus_estimates_from_identifiers(identifiers=["AAPL"], line_item="eps_normalized", period_type="quarterly", num_periods_backward=1)        

        Query: "Apple consensus EPS estimates for last 2 quarters and next 4 quarters using Capital IQ data."
        Function: get_consensus_estimates_from_identifiers(identifiers=["AAPL"], line_item="eps_normalized", period_type="quarterly", num_periods_backward=2, num_periods_forward=4)
    """).strip()

    @property
    def estimate_type(self) -> EstimateType:
        """The estimate type is consensus."""
        return EstimateType.consensus

    args_schema: Type[BaseModel] = GetConsensusEstimatesFromIdentifiersArgs


class GetGuidanceFromIdentifiers(GetEstimatesFromIdentifiers):
    name: str = "get_guidance_from_identifiers"
    description: str = dedent("""
        Get a single company-issued financial guidance (EPS, Revenue, EBITDA, etc.) for a list of identifiers. Returns Capital IQ data.
        Returns the most recent guidance provided by the company for future periods, or the final guidance issued before results were reported for past periods.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - If no time parameters are provided, next 4 quarters are retrieved by default.
        - To filter by time, use either absolute time (start_year, end_year, start_quarter, end_quarter) OR relative time (num_periods_forward, num_periods_backward)—but not both.

        Examples:
        Query: "Get revenue guidance for AAPL for 2026 using Capital IQ data."
        Function: get_guidance_from_identifiers(identifiers=["AAPL"], line_item="revenue", period_type="annual", start_year=2026, end_year=2026)

        Query: "Get revenue guidance for AAPL for the next 4 years using Capital IQ data."
        Function: get_guidance_from_identifiers(identifiers=["AAPL"], line_item="revenue", period_type="annual", num_periods_backward=0, num_periods_forward=4)

        Query: "Get revenue guidance for AAPL for the most recently announced quarter using Capital IQ data."
        Function: get_guidance_from_identifiers(identifiers=["AAPL"], line_item="revenue", period_type="quarterly", num_periods_backward=1, num_periods_forward=0)
    """).strip()

    @property
    def estimate_type(self) -> EstimateType:
        """The estimate type is guidance."""
        return EstimateType.guidance

    args_schema: Type[BaseModel] = GetGuidanceEstimatesFromIdentifiersArgs


class GetConsensusTargetPriceFromIdentifiersResp(ToolRespWithIdInfoAndErrors[ConsensusTargetPrice]):
    pass


class GetConsensusTargetPriceFromIdentifiers(KfinanceTool):
    name: str = "get_consensus_target_price_from_identifiers"
    description: str = dedent("""
        Get consensus analyst target price estimates for a list of identifiers. Returns Capital IQ data.
        Returns the current consensus analyst target price including high, low, mean, median, and standard deviation values.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.

        Examples:
        Query: "Get consensus target price for AAPL."
        Function: get_consensus_target_price_from_identifiers(identifiers=["AAPL"])

        Query: "Get consensus target price for AAPL and MSFT."
        Function: get_consensus_target_price_from_identifiers(identifiers=["AAPL", "MSFT"])
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
        Get analyst recommendations for a list of identifiers. Returns Capital IQ data.
        Returns the current consensus analyst recommendation breakdown including buy, hold, sell counts and overall analyst sentiment.
        If the user is asking for a company's rating, assume this means credit rating unless the user clearly asks for analyst ratings.

        Examples:
        Query: "Get analyst recommendations for AAPL."
        Function: get_analyst_recommendations_from_identifiers(identifiers=["AAPL"])

        Query: "Get analyst recommendations for AAPL and MSFT."
        Function: get_analyst_recommendations_from_identifiers(identifiers=["AAPL", "MSFT"])
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


async def get_estimates_from_identifiers(
    identifiers: list[str],
    line_item: str,
    estimate_type: EstimateType,
    httpx_client: httpx2.AsyncClient,
    period_type: EstimatePeriodType | None = None,
    fiscal_start_year: int | None = None,
    fiscal_end_year: int | None = None,
    fiscal_start_quarter: Literal[1, 2, 3, 4] | None = None,
    fiscal_end_quarter: Literal[1, 2, 3, 4] | None = None,
    num_periods_forward: int | None = None,
    num_periods_backward: int | None = None,
) -> GetCiqEstimatesFromIdentifiersResp:
    """Fetch estimates for all identifiers."""

    # First resolve identifiers to company IDs
    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    # Fetch line items for all resolved company IDs
    if id_triple_resp.company_ids:
        estimates_resp = await fetch_estimates_from_company_ids(
            company_ids=id_triple_resp.company_ids,
            line_item=line_item,
            estimate_type=estimate_type,
            httpx_client=httpx_client,
            period_type=period_type,
            fiscal_start_year=fiscal_start_year,
            fiscal_end_year=fiscal_end_year,
            fiscal_start_quarter=fiscal_start_quarter,
            fiscal_end_quarter=fiscal_end_quarter,
            num_periods_forward=num_periods_forward,
            num_periods_backward=num_periods_backward,
        )

        # Add any errors from the line item API, mapping company_id keys back to identifiers
        for company_id_str, error in estimates_resp.errors.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            errors.append(f"{original_identifier}: {error}")

        # Map results back to original identifiers
        identifier_to_results = {}
        for company_id_str, line_item_data in estimates_resp.results.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            identifier_to_results[original_identifier] = line_item_data

        results = identifier_to_results
    else:
        results = {}

    # If no date and multiple companies, only return the most recent value
    if (
        fiscal_start_year is None
        and fiscal_end_year is None
        and fiscal_start_quarter is None
        and fiscal_end_quarter is None
        and num_periods_forward is None
        and num_periods_backward is None
        and len(results) > 1
    ):
        for estimates_response in results.values():
            estimates_response.remove_all_periods_other_than_the_most_recent_one()

    resp_model = GetCiqEstimatesFromIdentifiersResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
        data_source="Capital IQ",
    )

    # Add explanatory notes
    insert_fiscal_period_notes(
        calendar_type=CalendarType.fiscal,  # Estimates are always fiscal
        period_type=period_type,
        resp_model=resp_model,
    )

    return resp_model


async def fetch_estimates_from_company_ids(
    company_ids: list[int],
    line_item: str,
    estimate_type: EstimateType,
    httpx_client: httpx2.AsyncClient,
    period_type: EstimatePeriodType | None = None,
    fiscal_start_year: int | None = None,
    fiscal_end_year: int | None = None,
    fiscal_start_quarter: Literal[1, 2, 3, 4] | None = None,
    fiscal_end_quarter: Literal[1, 2, 3, 4] | None = None,
    num_periods_forward: int | None = None,
    num_periods_backward: int | None = None,
) -> PostResponseWithLineItemMetadata[CiqEstimates]:
    """Fetch estimates for one company_id."""
    # Build query parameters
    params: dict[str, Any] = {
        "company_ids": company_ids,
        "line_item": line_item,
        "estimate_type": estimate_type.value,
    }

    if period_type is not None:
        params["period_type"] = period_type.value
    if fiscal_start_year is not None:
        params["fiscal_start_year"] = fiscal_start_year
    if fiscal_end_year is not None:
        params["fiscal_end_year"] = fiscal_end_year
    if fiscal_start_quarter is not None:
        params["fiscal_start_quarter"] = fiscal_start_quarter
    if fiscal_end_quarter is not None:
        params["fiscal_end_quarter"] = fiscal_end_quarter
    if num_periods_forward is not None:
        params["num_periods_forward"] = num_periods_forward
    if num_periods_backward is not None:
        params["num_periods_backward"] = num_periods_backward

    resp = await httpx_client.post(url="/estimates/", json=params)
    resp.raise_for_status()
    return PostResponseWithLineItemMetadata[CiqEstimates].model_validate(resp.json())


async def get_consensus_target_price_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx2.AsyncClient,
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
    httpx_client: httpx2.AsyncClient,
) -> SingleResultResp[ConsensusTargetPrice]:
    """Fetch consensus target price for one company_id."""
    resp = await httpx_client.get(url=f"/estimates/consensus_target_price/{company_id}")
    resp.raise_for_status()
    return SingleResultResp[ConsensusTargetPrice].model_validate(resp.json())


async def get_analyst_recommendations_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx2.AsyncClient,
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
    httpx_client: httpx2.AsyncClient,
) -> SingleResultResp[AnalystRecommendations]:
    """Fetch analyst recommendations for one company_id."""
    resp = await httpx_client.get(url=f"/estimates/analyst_recommendations/{company_id}")
    resp.raise_for_status()
    return SingleResultResp[AnalystRecommendations].model_validate(resp.json())
