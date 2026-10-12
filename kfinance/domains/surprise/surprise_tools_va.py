from textwrap import dedent
from typing import Any, Literal, Type, cast

import httpx2
from pydantic import Field, BaseModel

from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.models.date_and_period_models import EstimatePeriodType, NumPeriodsBackward
from kfinance.client.models.response_models import PostResponseWithLineItemMetadata
from kfinance.client.permission_models import Permission
from kfinance.domains.line_items.line_item_models import AlternativeLineItemMetadata, CalendarType
from kfinance.domains.line_items.response_notes import insert_source_link_note, insert_fiscal_period_notes
from kfinance.domains.surprise.surprise_models import VisibleAlphaSurprises
from kfinance.integrations.tool_calling.tool_calling_models import ToolRespWithIdInfoAndErrors, ToolArgsWithIdentifiers, \
    ValidQuarter, KfinanceTool


class GetVaSurpriseFromIdentifiersResp(ToolRespWithIdInfoAndErrors[VisibleAlphaSurprises]):
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, AlternativeLineItemMetadata] = Field(default_factory=dict)
    data_source: str


class GetVisibleAlphaSurprisesFromIdentifiersArgs(ToolArgsWithIdentifiers):
    period_type: EstimatePeriodType | None = Field(
        default=None, description="The period type (annual, semi-annual, or quarterly)."
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
        default=None,
        description="Starting quarter (1-4). Used when period_type is semi-annual or quarterly.",
    )
    end_quarter: ValidQuarter | None = Field(
        default=None,
        description="Ending quarter (1-4). Used when period_type is semi-annual or quarterly.",
    )
    estimate_search: str | None = Field(
        default=None,
        description="The financial metric, business measure, or quantitative data point to retrieve. Use descriptive natural language. Preserve the specificity of what the user asked for; keep any product, model, series, segment, or region qualifiers they named rather than generalizing to a broader metric. When the user names several distinct items, make a separate call per item using its specific name.",
    )
    calendar_type: CalendarType | None = Field(
        default=None,
        description="Fiscal year or calendar year. Use 'calendar' for calendar year references.",
    )
    num_periods_backward: NumPeriodsBackward | None = Field(
        default=None,
        description="The number of periods to look back from today (0-99).",
    )


class GetVisibleAlphaSurprisesFromIdentifiers(KfinanceTool):
    name: str = "get_visible_alpha_surprises_from_identifiers"
    description: str = dedent("""
        Get surprises for a list of identifiers. Returns Visible Alpha data. The surprise is the difference between the estimate just before the reporting date, and the actual reported value. 

        Returns the estimated value, the actual, and the percentage difference between them for each matched metric per period. Surprise data is only available for periods where financials have been reported.

        - For a ratio, percentage, or proportion, prefer a pre-computed ratio metric from the results or `top_ranked_alternatives`, if available, over fetching a single raw component.
        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - To fetch the most recent surprises, leave all time parameters as null.
        - To filter by time, use either absolute time (start_year, end_year, start_quarter, end_quarter) OR relative time (num_periods_backward)—but not both.

        Examples:
        Query: "Get EPS surprise for AAPL"
        Function: get_visible_alpha_surprises_from_identifiers(identifiers=["AAPL"], estimate_search="EPS", num_periods_backward=4)

        Query: "iPhone unit sales surprise for Apple for the last 4 quarters"
        Function: get_visible_alpha_surprises_from_identifiers(identifiers=["AAPL"], estimate_search="iPhone unit sales", period_type="quarterly", num_periods_backward=4)

        Query: "SAP revenue surprises for fiscal 2023 through 2025"
        Function: get_visible_alpha_surprises_from_identifiers(identifiers=["SAP"], estimate_search="revenue", period_type="annual", start_year=2023, end_year=2025)
        
        Query: "What was the beat/miss of TSLA model 3 revenue over the last 8 quarters?"
        Function: get_visible_alpha_surprises_from_identifiers(identifiers["TSLA"], estimate_search="model 3 revenue", period_type="quarterly", num_periods_backward=8)
        
        Query: "Show me MCD's diluted EPS surprise historically"
        Function: get_visible_alpha_surprises_from_identifiers(identifiers["MCD"], estimate_search="diluted EPS", num_periods_backward=4)
        
        Query: "Are Nvidia’s data center beats accelerating, decelerating, or becoming more volatile over time?"
        Function: get_visible_alpha_surprises_from_identifiers(identifiers["Nvidia"], estimate_search="data center", num_periods_backward=12)
    """).strip()
    args_schema: Type[BaseModel] = GetVisibleAlphaSurprisesFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.VisibleAlphaPermission}

    async def _arun(
        self,
        identifiers: list[str],
        period_type: EstimatePeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal["1", "2", "3", "4"] | None = None,
        end_quarter: Literal["1", "2", "3", "4"] | None = None,
        num_periods_backward: int | None = None,
        estimate_search: str | None = None,
        calendar_type: CalendarType | None = None,
    ) -> GetVaSurpriseFromIdentifiersResp:
        """"""
        return await get_visible_alpha_surprises_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=cast(Literal[1, 2, 3, 4], int(start_quarter)) if start_quarter else None,
            end_quarter=cast(Literal[1, 2, 3, 4], int(end_quarter)) if end_quarter else None,
            num_periods_backward=num_periods_backward,
            estimate_search=estimate_search,
            calendar_type=calendar_type,
        )


async def fetch_visible_alpha_surprises_from_company_ids(
    company_ids: list[int],
    httpx_client: httpx2.AsyncClient,
    period_type: EstimatePeriodType | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    start_quarter: Literal[1, 2, 3, 4] | None = None,
    end_quarter: Literal[1, 2, 3, 4] | None = None,
    num_periods_backward: int | None = None,
    estimate_search: str | None = None,
    calendar_type: CalendarType | None = None,
) -> PostResponseWithLineItemMetadata[VisibleAlphaSurprises]:
    """Fetch surprises for a list of company IDs using Visible Alpha as the data source."""
    payload: dict[str, Any] = {
        "company_ids": company_ids,
    }

    if period_type is not None:
        payload["period_type"] = period_type.value
    if start_year is not None:
        payload["start_year"] = start_year
    if end_year is not None:
        payload["end_year"] = end_year
    if start_quarter is not None:
        payload["start_quarter"] = start_quarter
    if end_quarter is not None:
        payload["end_quarter"] = end_quarter
    if num_periods_backward is not None:
        payload["num_periods_backward"] = num_periods_backward
    if estimate_search is not None:
        payload["estimate_search"] = estimate_search
    if calendar_type is not None:
        payload["calendar_type"] = calendar_type.value

    resp = await httpx_client.post(url="/surprise/visible_alpha", json=payload)
    resp.raise_for_status()

    return PostResponseWithLineItemMetadata[VisibleAlphaSurprises].model_validate(resp.json())


async def get_visible_alpha_surprises_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx2.AsyncClient,
    period_type: EstimatePeriodType | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    start_quarter: Literal[1, 2, 3, 4] | None = None,
    end_quarter: Literal[1, 2, 3, 4] | None = None,
    num_periods_backward: int | None = None,
    estimate_search: str | None = None,
    calendar_type: CalendarType | None = None,
) -> GetVaSurpriseFromIdentifiersResp:
    """Fetch surprises for all identifiers using Visible Alpha as the data source."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    metadata: dict[str, AlternativeLineItemMetadata] = {}
    if id_triple_resp.company_ids:
        surprises_resp = await fetch_visible_alpha_surprises_from_company_ids(
            company_ids=id_triple_resp.company_ids,
            httpx_client=httpx_client,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
            num_periods_backward=num_periods_backward,
            estimate_search=estimate_search,
            calendar_type=calendar_type,
        )

        for company_id_str, error in surprises_resp.errors.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            errors.append(f"{original_identifier}: {error}")

        identifier_to_results = {}
        for company_id_str, estimates_data in surprises_resp.results.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            identifier_to_results[original_identifier] = estimates_data

        for company_id_str, meta in surprises_resp.metadata.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            metadata[original_identifier] = meta

        results = identifier_to_results
    else:
        results = {}

    resp_model = GetVaSurpriseFromIdentifiersResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
        metadata=metadata,
        data_source="Visible Alpha",
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
            " estimate name against your intent and the listed"
            " `top_ranked_alternatives`. If any alternative is a closer match to"
            " what was asked, you MUST call the tool again using that exact"
            " alternative name as the `estimate_search` parameter before answering."
        )

    return resp_model
