from textwrap import dedent
from typing import Literal, Type

from pydantic import BaseModel, Field

from kfinance.client.models.date_and_period_models import NumPeriods, NumPeriodsBack, PeriodType
from kfinance.client.permission_models import Permission
from kfinance.domains.line_items.line_item_models import CalendarType
from kfinance.domains.statements.statement_models import StatementsResp, StatementType
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

    def _run(
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
        """Sample response:

        {
            'results': {
                'SPGI': {
                    'currency': 'USD',
                    'periods': {
                        'CY2020': {
                            'period_end_date': '2020-12-31',
                            'num_months': 12,
                            'statements': [
                                {
                                    'name': 'Income Statement',
                                    'line_items': [
                                        {
                                            'name': 'Revenues',
                                            'value': 7442000000.0,
                                            'sources': [
                                                {
                                                    'type': 'doc-viewer statement',
                                                    'url': 'https://www.capitaliq.spglobal.com/...'
                                                }
                                            ]
                                        },
                                        {
                                            'name': 'Total Revenues',
                                            'value': 7442000000.0
                                        }
                                    ]
                                }
                            ]
                        },
                        'CY2021': {
                            'period_end_date': '2021-12-31',
                            'num_months': 12,
                            'statements': [
                                {
                                    'name': 'Income Statement',
                                    'line_items': [
                                        {
                                            'name': 'Revenues',
                                            'value': 8243000000.0
                                        },
                                        {
                                            'name': 'Total Revenues',
                                            'value': 8243000000.0
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            },
            'errors': ['No identification triple found for the provided identifier: NON-EXISTENT of type: ticker']
        }
        """
        api_client = self.kfinance_client.kfinance_api_client

        # First resolve identifiers to company IDs
        ids_response = api_client.unified_fetch_id_triples(identifiers)

        # Call the simplified fetch_statement API with company IDs
        response = api_client.fetch_statement(
            company_ids=ids_response.company_ids,
            statement_type=statement.value,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
            calendar_type=calendar_type,
            num_periods=num_periods,
            num_periods_back=num_periods_back,
        )

        identifier_to_results = {}
        for company_id_str, statement_resp in response.results.items():
            original_identifier = ids_response.get_identifier_from_company_id(int(company_id_str))
            identifier_to_results[original_identifier] = statement_resp

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

        all_errors = list(ids_response.errors.values()) + list(response.errors.values())

        return GetFinancialStatementFromIdentifiersResp(
            results=identifier_to_results, errors=all_errors
        )
