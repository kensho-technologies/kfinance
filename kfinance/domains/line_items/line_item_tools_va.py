from textwrap import dedent
from typing import Any, Literal, Type

import httpx
from pydantic import BaseModel, Field

from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.models.date_and_period_models import (
    EstimatePeriodType,
    NumPeriods,
    NumPeriodsBack,
)
from kfinance.client.permission_models import Permission
from kfinance.domains.line_items.line_item_models import (
    AlternativeLineItemMetadata,
    CalendarType,
    LineItemResp,
)
from kfinance.domains.line_items.response_notes import (
    insert_fiscal_period_notes,
    insert_source_link_note,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithIdInfoAndErrors,
    ValidQuarter,
)


class GetVisibleAlphaFinancialLineItemFromIdentifiersArgs(ToolArgsWithIdentifiers):
    line_item: str = Field(
        description="The financial metric, business measure, or quantitative data point to retrieve. Use descriptive natural language. Preserve the specificity of what the user asked for; keep any product, model, series, segment, or region qualifiers they named rather than generalizing to a broader metric. When the user names several distinct items, make a separate call per item using its specific name."
    )
    period_type: EstimatePeriodType | None = Field(
        default=None, description="The period type (annual or quarterly)"
    )
    start_year: int | None = Field(
        default=None,
        description="The starting year for the data range. Use null for the most recent data.",
    )
    end_year: int | None = Field(
        default=None,
        description="The ending year for the data range. Use null for the most recent data.",
    )
    start_quarter: ValidQuarter | None = Field(
        default=None, description="Starting quarter (1-4). Only used when period_type is quarterly."
    )
    end_quarter: ValidQuarter | None = Field(
        default=None, description="Ending quarter (1-4). Only used when period_type is quarterly."
    )
    calendar_type: CalendarType | None = Field(
        default=None, description="Fiscal year or calendar year"
    )
    num_periods: NumPeriods | None = Field(
        default=None, description="The number of periods to retrieve data for (1-99)"
    )
    num_periods_back: NumPeriodsBack | None = Field(
        default=None,
        description="The end period of the data range expressed as number of periods back relative to the present period (0-99)",
    )
    currency: str | None = Field(
        default=None,
        description="ISO 4217 currency code to return values in (e.g. 'USD', 'EUR'). Defaults to the reporting currency if not specified.",
    )


class PostResponseWithMetadata(BaseModel):
    results: dict[str, LineItemResp]
    errors: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, AlternativeLineItemMetadata] = Field(default_factory=dict)
    data_source: str | None = None


class GetVisibleAlphaFinancialLineItemFromIdentifiersResp(
    ToolRespWithIdInfoAndErrors[LineItemResp]
):
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, AlternativeLineItemMetadata] = Field(default_factory=dict)
    data_source: str = "Visible Alpha"


class GetFinancialLineItemFromIdentifiersVa(KfinanceTool):
    name: str = "get_financial_line_item_from_identifiers"
    description: str = dedent("""
        Get any reported financial metric for a list of identifiers: including company-level, segment-level, product-level, and geographic metrics, as well as ratios and per-unit figures. This is the primary tool for a specific named metric. The freeform `line_item` query is matched semantically against a large catalog, so phrase it descriptively and prefer this tool before segment-, statement-, or estimate-specific tools.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - To fetch the most recent value, leave all time parameters as null.
        - To filter by time, use either absolute time (start_year, end_year, start_quarter, end_quarter) OR relative time (num_periods, num_periods_back)—but not both.
        - Set calendar_type based on how the query references the time period—use "fiscal" for fiscal year references and "calendar" for calendar year references.
        - When calendar_type=None, it defaults to 'fiscal'.
        - Exception: with multiple identifiers and absolute time, calendar_type=None defaults to 'calendar' for cross-company comparability; calendar_type='fiscal' returns fiscal data but should not be compared across companies since fiscal years have different end dates.

        Examples:
        Query: "Get MSFT and AAPL revenue and gross profit quarterly"
        Function: get_financial_line_item_from_identifiers(line_item="total revenue", identifiers=["MSFT", "AAPL"], period_type="quarterly")
        Function: get_financial_line_item_from_identifiers(line_item="gross profit", identifiers=["MSFT", "AAPL"], period_type="quarterly")

        Query: "How much money did TSMC make for 5nm wafers"
        Function: get_financial_line_item_from_identifiers(line_item="revenue from 5nm wafers", identifiers=["TSMC"], period_type="annual")

        Query: "Tesla automotive gross margin for FY2023"
        Function: get_financial_line_item_from_identifiers(line_item="automotive gross margin", identifiers=["Tesla"], period_type="annual", calendar_type="fiscal", start_year=2023, end_year=2023)

        Query: "Most recent three quarters except one ppe for Exxon and Hasbro"
        Function: get_financial_line_item_from_identifiers(line_item="property plant and equipment", period_type="quarterly", num_periods=2, num_periods_back=1, identifiers=["Exxon", "Hasbro"])
    """).strip()
    args_schema: Type[BaseModel] = GetVisibleAlphaFinancialLineItemFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.VisibleAlphaPermission}

    async def _arun(
        self,
        identifiers: list[str],
        line_item: str,
        period_type: EstimatePeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
        calendar_type: CalendarType | None = None,
        num_periods: int | None = None,
        num_periods_back: int | None = None,
        currency: str | None = None,
    ) -> GetVisibleAlphaFinancialLineItemFromIdentifiersResp:
        """"""
        return await get_visible_alpha_financial_line_item_from_identifiers(
            identifiers=identifiers,
            line_item=line_item,
            httpx_client=self.kfinance_client.httpx_client,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
            calendar_type=calendar_type,
            num_periods=num_periods,
            num_periods_back=num_periods_back,
            currency=currency,
        )


async def fetch_visible_alpha_line_item_from_company_ids(
    company_ids: list[int],
    line_item: str,
    httpx_client: httpx.AsyncClient,
    period_type: EstimatePeriodType | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    start_quarter: Literal[1, 2, 3, 4] | None = None,
    end_quarter: Literal[1, 2, 3, 4] | None = None,
    calendar_type: CalendarType | None = None,
    num_periods: int | None = None,
    num_periods_back: int | None = None,
    currency: str | None = None,
) -> PostResponseWithMetadata:
    """Fetch line items for a list of company IDs using Visible Alpha as the data source."""
    params: dict[str, Any] = {
        "company_ids": company_ids,
        "line_item": line_item,
    }

    if period_type is not None:
        params["period_type"] = period_type.value
    if start_year is not None:
        params["start_year"] = start_year
    if end_year is not None:
        params["end_year"] = end_year
    if start_quarter is not None:
        params["start_quarter"] = start_quarter
    if end_quarter is not None:
        params["end_quarter"] = end_quarter
    if calendar_type is not None:
        params["calendar_type"] = calendar_type.value
    if num_periods is not None:
        params["num_periods"] = num_periods
    if num_periods_back is not None:
        params["num_periods_back"] = num_periods_back
    if currency is not None:
        params["currency"] = currency

    resp = await httpx_client.post(url="/line_item/", json=params)
    resp.raise_for_status()

    return PostResponseWithMetadata.model_validate(resp.json())


async def get_visible_alpha_financial_line_item_from_identifiers(
    identifiers: list[str],
    line_item: str,
    httpx_client: httpx.AsyncClient,
    period_type: EstimatePeriodType | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    start_quarter: Literal[1, 2, 3, 4] | None = None,
    end_quarter: Literal[1, 2, 3, 4] | None = None,
    calendar_type: CalendarType | None = None,
    num_periods: int | None = None,
    num_periods_back: int | None = None,
    currency: str | None = None,
) -> GetVisibleAlphaFinancialLineItemFromIdentifiersResp:
    """Fetch financial line items for all identifiers using Visible Alpha as the data source."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    metadata: dict[str, AlternativeLineItemMetadata] = {}
    if id_triple_resp.company_ids:
        line_item_resp = await fetch_visible_alpha_line_item_from_company_ids(
            company_ids=id_triple_resp.company_ids,
            line_item=line_item,
            httpx_client=httpx_client,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
            calendar_type=calendar_type,
            num_periods=num_periods,
            num_periods_back=num_periods_back,
            currency=currency,
        )

        for company_id_str, error in line_item_resp.errors.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            errors.append(f"{original_identifier}: {error}")

        identifier_to_results = {}
        for company_id_str, line_item_data in line_item_resp.results.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            line_item_data.data_source = "Visible Alpha"
            identifier_to_results[original_identifier] = line_item_data

        for company_id_str, meta in line_item_resp.metadata.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            metadata[original_identifier] = meta

        results = identifier_to_results
    else:
        results = {}

    if (
        start_year is None
        and end_year is None
        and start_quarter is None
        and end_quarter is None
        and num_periods is None
        and num_periods_back is None
        and len(results) > 1
    ):
        for line_item_response in results.values():
            line_item_response.remove_all_periods_other_than_the_most_recent_one()

    resp_model = GetVisibleAlphaFinancialLineItemFromIdentifiersResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
        metadata=metadata,
    )

    insert_source_link_note(resp_model)
    insert_fiscal_period_notes(
        calendar_type=calendar_type,
        period_type=period_type,
        resp_model=resp_model,
    )

    if metadata:
        resp_model.notes.append(
            "The result may not be an exact match. ALWAYS compare the returned"
            " `line_item.name` against your intent and the listed"
            " `top_ranked_alternatives`. If any alternative is a closer match to"
            " what was asked, you MUST call the tool again using that exact"
            " alternative name as the `line_item` query before answering."
        )

    return resp_model
