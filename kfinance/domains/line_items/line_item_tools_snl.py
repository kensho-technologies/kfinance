from collections import defaultdict
from textwrap import dedent
from typing import Any, Literal, Type, cast

import httpx2
from pydantic import BaseModel, Field

from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.models.date_and_period_models import PeriodType
from kfinance.client.permission_models import Permission
from kfinance.domains.line_items.line_item_models import CalendarType, LineItemResp
from kfinance.domains.line_items.line_item_tools import (
    BaseFinancialLineItemFromIdentifiersArgs,
)
from kfinance.domains.line_items.response_notes import insert_source_link_note
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolRespWithIdInfoAndErrors,
)


class GetSnlBankRegFinancialLineItemFromIdentifiersArgs(BaseFinancialLineItemFromIdentifiersArgs):
    line_item_search: str = Field(
        description=(
            "The financial metric or regulatory data point to retrieve from bank regulatory "
            "filings (Call Reports, FFIEC). Use descriptive natural language. Preserve the "
            "specificity of what the user asked for. When the user names several distinct items, "
            "make a separate call per item."
        ),
    )
    period_type: PeriodType | None = Field(
        default=None, description="The period type (annual, quarterly, ltm, or ytd)"
    )


class GetSnlBankRegFinancialLineItemFromIdentifiersResp(ToolRespWithIdInfoAndErrors[LineItemResp]):
    notes: list[str] = Field(default_factory=list)
    data_source: str
    requested_line_item: str
    line_item_matches: list[dict] = Field(default_factory=list)


class GetSnlBankRegFinancialLineItemFromIdentifiers(KfinanceTool):
    name: str = "get_snl_bankreg_financial_line_item_from_identifiers"
    description: str = dedent("""
        Get any reported bank regulatory (BankReg) financial metric for a list of identifiers
        using semantic search. The freeform `line_item_search` query is matched against SNL's
        BankReg dataitem catalog. Returns S&P SNL data from Call Reports and FFIEC filings.

        For banks and other financial institutions, prefer this tool over
        `get_financial_line_item_from_identifiers` (Capital IQ) — BankReg has much deeper
        coverage of regulatory metrics, capital ratios, and bank-specific line items.
        For non-bank companies, use `get_visible_alpha_financial_line_item_from_identifiers`
        (Visible Alpha) or `get_financial_line_item_from_identifiers` (Capital IQ) instead.

        - `line_item_matches` in the response lists the top semantic matches with which
          companies report each. Check it to verify the selected metric is correct and to
          find alternatives if the top match is not what was intended.
        - If a company returns an error, it may not be a BankReg filer.
        - Returns reported (actual, historical) regulatory filing figures only.
        - BankReg fiscal and calendar periods are always aligned: FY2026Q2 = the quarter
          ending 2026-06-30. `calendar_type` only changes the period key prefix (FY vs CY).
        - Only dollar amounts carry a currency; ratios, counts, and percentages do not.
        - When possible, pass multiple identifiers in a single call.
        - To fetch the most recent value, leave all time parameters as null.
        - To filter by time, use either absolute time (start_year, end_year, start_quarter,
          end_quarter) OR relative time (num_periods, num_periods_back)—but not both.

        Examples:
        Query: "Total revenue for JPMorgan Chase quarterly"
        Function: get_snl_bankreg_financial_line_item_from_identifiers(line_item_search="total revenue", identifiers=["JPMorgan Chase"], period_type="quarterly")

        Query: "Total deposits for JPM bank"
        Note: "JPM bank" likely refers to the subsidiary JPMorgan Chase Bank, N.A. — use the full name so identifier resolution finds the right entity.
        Function: get_snl_bankreg_financial_line_item_from_identifiers(line_item_search="total deposits", identifiers=["JPMorgan Chase Bank, N.A."])

        Query: "Tier 1 capital ratio for Wells Fargo and Bank of America for the last 5 years"
        Function: get_snl_bankreg_financial_line_item_from_identifiers(line_item_search="tier 1 capital ratio", identifiers=["Wells Fargo", "Bank of America"], period_type="annual", num_periods=5)

        Query: "Net interest income for Citibank annual FY2025"
        Function: get_snl_bankreg_financial_line_item_from_identifiers(line_item_search="net interest income", identifiers=["Citibank"], period_type="annual", calendar_type="fiscal", start_year=2025, end_year=2025)
    """).strip()
    args_schema: Type[BaseModel] = GetSnlBankRegFinancialLineItemFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.OnlyStaffPermission}

    async def _arun(
        self,
        identifiers: list[str],
        line_item_search: str,
        period_type: PeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal["1", "2", "3", "4"] | None = None,
        end_quarter: Literal["1", "2", "3", "4"] | None = None,
        calendar_type: CalendarType | None = None,
        num_periods: int | None = None,
        num_periods_back: int | None = None,
    ) -> GetSnlBankRegFinancialLineItemFromIdentifiersResp:
        """"""
        return await get_snl_bankreg_financial_line_item_from_identifiers(
            identifiers=identifiers,
            line_item_search=line_item_search,
            httpx_client=self.kfinance_client.httpx_client,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=cast(Literal[1, 2, 3, 4], int(start_quarter)) if start_quarter else None,
            end_quarter=cast(Literal[1, 2, 3, 4], int(end_quarter)) if end_quarter else None,
            calendar_type=calendar_type,
            num_periods=num_periods,
            num_periods_back=num_periods_back,
        )


async def fetch_snl_bankreg_line_item_from_company_ids(
    company_ids: list[int],
    line_item_search: str,
    httpx_client: httpx2.AsyncClient,
    period_type: PeriodType | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    start_quarter: Literal[1, 2, 3, 4] | None = None,
    end_quarter: Literal[1, 2, 3, 4] | None = None,
    calendar_type: CalendarType | None = None,
    num_periods: int | None = None,
    num_periods_back: int | None = None,
) -> dict[str, Any]:
    """Fetch SNL BankReg line items for a list of company IDs. Returns the raw JSON response."""
    params: dict[str, Any] = {
        "company_ids": company_ids,
        "line_item_search": line_item_search,
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

    resp = await httpx_client.post(url="/line_item/snl", json=params)
    resp.raise_for_status()

    return resp.json()


async def get_snl_bankreg_financial_line_item_from_identifiers(
    identifiers: list[str],
    line_item_search: str,
    httpx_client: httpx2.AsyncClient,
    period_type: PeriodType | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    start_quarter: Literal[1, 2, 3, 4] | None = None,
    end_quarter: Literal[1, 2, 3, 4] | None = None,
    calendar_type: CalendarType | None = None,
    num_periods: int | None = None,
    num_periods_back: int | None = None,
) -> GetSnlBankRegFinancialLineItemFromIdentifiersResp:
    """Fetch SNL BankReg financial line items for all identifiers."""
    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: dict[str, list[str]] = defaultdict(list)
    for identifier, error in id_triple_resp.errors.items():
        errors[identifier].append(error)

    line_item_matches: list[dict] = []
    if id_triple_resp.company_ids:
        raw_resp = await fetch_snl_bankreg_line_item_from_company_ids(
            company_ids=id_triple_resp.company_ids,
            line_item_search=line_item_search,
            httpx_client=httpx_client,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
            calendar_type=calendar_type,
            num_periods=num_periods,
            num_periods_back=num_periods_back,
        )

        server_errors: dict[str, str] = raw_resp.get("errors", {})
        for company_id_str, error in server_errors.items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            errors[original_identifier].append(error)

        identifier_to_results: dict[str, LineItemResp] = {}
        for company_id_str, line_item_data in raw_resp.get("results", {}).items():
            original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
            identifier_to_results[original_identifier] = LineItemResp.model_validate(line_item_data)

        results = identifier_to_results
        requested_line_item = raw_resp.get("requested_line_item") or line_item_search
        line_item_matches = [
            {
                "dataitem_id": match["dataitem_id"],
                "name": match["name"],
                "description": match["description"],
                "identifiers": [
                    id_triple_resp.get_identifier_from_company_id(cid)
                    for cid in match.get("company_ids", [])
                ],
            }
            for match in (raw_resp.get("line_item_matches") or [])
        ]
    else:
        results = {}
        requested_line_item = line_item_search

    # When no date filters and multiple companies, only return the most recent value.
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

    resp_model = GetSnlBankRegFinancialLineItemFromIdentifiersResp(
        identifier_results=results,
        identifier_errors=errors,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        data_source="SNL",
        requested_line_item=requested_line_item,
        line_item_matches=line_item_matches,
    )

    insert_source_link_note(resp_model)

    if line_item_matches:
        resp_model.notes.append(
            "The result may not be an exact match. ALWAYS compare the returned"
            " `requested_line_item` against your intent and the listed"
            " `line_item_matches`. If any alternative is a closer match to"
            " what was asked, you MUST call the tool again using that exact"
            " alternative name as the `line_item_search` query before answering."
        )

    return resp_model
