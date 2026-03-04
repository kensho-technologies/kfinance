from textwrap import dedent
from typing import Literal, Type, Any

import httpx
from pydantic import BaseModel, Field

from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.models.date_and_period_models import NumPeriods, NumPeriodsBack, PeriodType
from kfinance.client.permission_models import Permission
from kfinance.domains.line_items.line_item_models import CalendarType
from kfinance.domains.statements.statement_models import (
    StatementsBatchResp,
    StatementsResp,
    StatementType,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
    ValidQuarter,
)


class GetFinancialStatementFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    statement: StatementType
    period_type: PeriodType | None = Field(
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


class GetFinancialStatementFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, StatementsResp]  # identifier -> response


class GetFinancialStatementFromIdentifiers(KfinanceTool):
    name: str = "get_financial_statement_from_identifiers"
    description: str = dedent("""
        Get a financial statement (balance_sheet, income_statement, or cashflow) for a group of identifiers.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - To fetch the most recent statement, leave all time parameters as null.
        - To filter by time, use either absolute time (start_year, end_year, start_quarter, end_quarter) OR relative time (num_periods, num_periods_back)—but not both.
        - Set calendar_type based on how the query references the time period—use "fiscal" for fiscal year references and "calendar" for calendar year references.
        - When calendar_type=None, it defaults to 'fiscal'.
        - Exception: with multiple identifiers and absolute time, calendar_type=None defaults to 'calendar' for cross-company comparability; calendar_type='fiscal' returns fiscal data but should not be compared across companies since fiscal years have different end dates.

        Examples:
        Query: "Fetch the balance sheets of Bank of America and Goldman Sachs for 2024"
        Function: get_financial_statement_from_identifiers(identifiers=["Bank of America", "Goldman Sachs"], statement="balance_sheet", period_type="annual", start_year=2024, end_year=2024)

        Query: "Get income statements for NEE and DUK"
        Function: get_financial_statement_from_identifiers(identifiers=["NEE", "DUK"], statement="income_statement")

        Query: "Q2 2023 cashflow for XOM"
        Function: get_financial_statement_from_identifiers(identifiers=["XOM"], statement="cashflow", period_type="quarterly", start_year=2023, end_year=2023, start_quarter=2, end_quarter=2)

        Query: "What is the balance sheet for The New York Times for the past 7 years except for the most recent 2 years?"
        Function: get_financial_statement_from_identifiers(statement="balance_sheet", num_periods=5, num_periods_back=2, identifiers=["NYT"])

        Query: "What are the annual income statement for the calendar years between 2013 and 2016 for BABA and W?"
        Function: get_financial_statement_from_identifiers(statement="income_statement", period_type="annual", calendar_type="calendar", start_year=2013, end_year=2016, identifiers=["BABA", "W"])
    """).strip()
    args_schema: Type[BaseModel] = GetFinancialStatementFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {
        Permission.StatementsPermission,
        Permission.PrivateCompanyFinancialsPermission,
    }

    async def _arun(
        self,
        identifiers: list[str],
        statement: StatementType,
        period_type: PeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
        calendar_type: CalendarType | None = None,
        num_periods: int | None = None,
        num_periods_back: int | None = None,
    ) -> GetFinancialStatementFromIdentifiersResp:
        """"""
        return await get_financial_statement_from_identifiers(
            identifiers=identifiers,
            statement=statement,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
            calendar_type=calendar_type,
            num_periods=num_periods,
            num_periods_back=num_periods_back,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def get_financial_statement_from_identifiers(
    identifiers: list[str],
    statement: StatementType,
    httpx_client: httpx.AsyncClient,
    period_type: PeriodType | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    start_quarter: Literal[1, 2, 3, 4] | None = None,
    end_quarter: Literal[1, 2, 3, 4] | None = None,
    calendar_type: CalendarType | None = None,
    num_periods: int | None = None,
    num_periods_back: int | None = None,
) -> GetFinancialStatementFromIdentifiersResp:
    """Fetch financial statements for all identifiers."""

    # First resolve identifiers to company IDs
    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    # Call the statements API with company IDs
    statements_resp = await fetch_statements_from_company_ids(
        company_ids=id_triple_resp.company_ids,
        statement_type=statement.value,
        period_type=period_type,
        start_year=start_year,
        end_year=end_year,
        start_quarter=start_quarter,
        end_quarter=end_quarter,
        calendar_type=calendar_type,
        num_periods=num_periods,
        num_periods_back=num_periods_back,
        httpx_client=httpx_client,
    )

    # Add any errors from the statements API
    errors.extend(statements_resp.errors)

    # Map results back to original identifiers
    identifier_to_results = {}
    for company_id_str, statement_data in statements_resp.results.items():
        original_identifier = id_triple_resp.get_identifier_from_company_id(int(company_id_str))
        identifier_to_results[original_identifier] = statement_data

    # If no date and multiple companies, only return the most recent value.
    # By default, we return 5 years of data, which can be too much when
    # returning data for many companies.
    if (
        start_year is None
        and end_year is None
        and start_quarter is None
        and end_quarter is None
        and num_periods is None
        and num_periods_back is None
        and len(identifier_to_results) > 1
    ):
        for result in identifier_to_results.values():
            result.remove_all_periods_other_than_the_most_recent_one()

    return GetFinancialStatementFromIdentifiersResp(results=identifier_to_results, errors=errors)


async def fetch_statements_from_company_ids(
    company_ids: list[int],
    statement_type: str,
    httpx_client: httpx.AsyncClient,
    period_type: PeriodType | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    start_quarter: Literal[1, 2, 3, 4] | None = None,
    end_quarter: Literal[1, 2, 3, 4] | None = None,
    calendar_type: CalendarType | None = None,
    num_periods: int | None = None,
    num_periods_back: int | None = None,
) -> StatementsBatchResp:
    """Fetch statements data from the API for multiple company IDs."""

    # Prepare the request payload
    payload: dict[str, Any] = {
        "company_ids": company_ids,
        "statement_type": statement_type,
    }

    # Add optional parameters if they are not None
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

    url = "/statements/"
    resp = await httpx_client.post(url=url, json=payload)

    return StatementsBatchResp.model_validate(resp.json())
