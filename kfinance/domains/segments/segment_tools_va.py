from textwrap import dedent
from typing import Any, Literal, Type

import httpx
from pydantic import BaseModel, Field

from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.models.date_and_period_models import EstimatePeriodType
from kfinance.client.models.response_models import PostResponse
from kfinance.client.permission_models import Permission
from kfinance.domains.line_items.line_item_models import CalendarType
from kfinance.domains.line_items.response_notes import insert_fiscal_period_notes
from kfinance.domains.segments.segment_models import SegmentsResp, SegmentType
from kfinance.domains.segments.segment_tools import (
    BaseSegmentsFromIdentifiersArgs,
    GetSegmentsFromIdentifiersResp,
)
from kfinance.integrations.tool_calling.tool_calling_models import KfinanceTool


class GetVisibleAlphaSegmentsFromIdentifiersArgs(BaseSegmentsFromIdentifiersArgs):
    period_type: EstimatePeriodType | None = Field(
        default=None, description="The period type (annual, semi-annual, or quarterly)."
    )
    currency: str | None = Field(
        default=None,
        description="ISO 4217 currency code to return values in (e.g. 'USD', 'EUR'). Defaults to the reporting currency if not specified.",
    )


class GetVisibleAlphaSegmentsFromIdentifiers(KfinanceTool):
    name: str = "get_visible_alpha_segments_from_identifiers"
    description: str = dedent("""
        Get the templated business or geographic segments associated with a list of identifiers.

        Use only for a full segment breakdown, not for specific segment metrics.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - To fetch the most recent segment data, leave all time parameters as null.
        - To filter by time, use either absolute time (start_year, end_year, start_quarter, end_quarter) OR relative time (num_periods, num_periods_back)—but not both.
        - Set calendar_type based on how the query references the time period—use "fiscal" for fiscal year references and "calendar" for calendar year references.
        - When calendar_type=None, it defaults to 'fiscal'.
        - Exception: with multiple identifiers and absolute time, calendar_type=None defaults to 'calendar' for cross-company comparability; calendar_type='fiscal' returns fiscal data but should not be compared across companies since fiscal years have different end dates.

        Examples:
        Query: "What are the business segments for AT&T?"
        Function: get_segments_from_identifiers(identifiers=["AT&T"], segment_type="business")

        Query: "Get most recent geographic segments for Pfizer and JNJ"
        Function: get_segments_from_identifiers(identifiers=["Pfizer", "JNJ"], segment_type="geographic")

        Query: "What are the ltm business segments for SPGI for the last three calendar quarters but one?"
        Function: get_segments_from_identifiers(segment_type="business", period_type="ltm", calendar_type="calendar", num_periods=2, num_periods_back=1, identifiers=["SPGI"])

        Query: "Get Apple's business segments in EUR"
        Function: get_segments_from_identifiers(identifiers=["AAPL"], segment_type="business", currency="EUR")
    """).strip()
    args_schema: Type[BaseModel] = GetVisibleAlphaSegmentsFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.VisibleAlphaPermission}

    async def _arun(
        self,
        identifiers: list[str],
        segment_type: SegmentType,
        period_type: EstimatePeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
        calendar_type: CalendarType | None = None,
        num_periods: int | None = None,
        num_periods_back: int | None = None,
        currency: str | None = None,
    ) -> GetSegmentsFromIdentifiersResp:
        """"""
        return await get_visible_alpha_segments_from_identifiers(
            identifiers=identifiers,
            segment_type=segment_type,
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


async def fetch_visible_alpha_segments_from_company_ids(
    company_ids: list[int],
    segment_type: SegmentType,
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
) -> PostResponse[SegmentsResp]:
    """Fetch segments for a list of company IDs using Visible Alpha as the data source."""
    payload: dict[str, Any] = {
        "company_ids": company_ids,
        "segment_type": segment_type.value,
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
    if calendar_type is not None:
        payload["calendar_type"] = calendar_type.value
    if num_periods is not None:
        payload["num_periods"] = num_periods
    if num_periods_back is not None:
        payload["num_periods_back"] = num_periods_back
    if currency is not None:
        payload["currency"] = currency

    resp = await httpx_client.post(url="/segments/visible_alpha", json=payload)
    resp.raise_for_status()

    return PostResponse[SegmentsResp].model_validate(resp.json())


async def get_visible_alpha_segments_from_identifiers(
    identifiers: list[str],
    segment_type: SegmentType,
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
) -> GetSegmentsFromIdentifiersResp:
    """Fetch segments for all identifiers using Visible Alpha as the data source."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    if id_triple_resp.company_ids:
        segments_resp = await fetch_visible_alpha_segments_from_company_ids(
            company_ids=id_triple_resp.company_ids,
            segment_type=segment_type,
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

        for company_id_str, error in segments_resp.errors.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            errors.append(f"{original_identifier}: {error}")

        identifier_to_results = {}
        for company_id_str, segments_data in segments_resp.results.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            identifier_to_results[original_identifier] = segments_data

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
        for segments_response in results.values():
            segments_response.remove_all_periods_other_than_the_most_recent_one()

    resp_model = GetSegmentsFromIdentifiersResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
        data_source="Visible Alpha",
    )

    insert_fiscal_period_notes(
        calendar_type=calendar_type,
        period_type=period_type,
        resp_model=resp_model,
    )

    return resp_model
