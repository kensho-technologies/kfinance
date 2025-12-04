from textwrap import dedent
from typing import Literal, Type

from pydantic import BaseModel, Field

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.models.date_and_period_models import NumPeriods, NumPeriodsBack, PeriodType
from kfinance.client.permission_models import Permission
from kfinance.domains.line_items.line_item_models import CalendarType
from kfinance.domains.statements.statement_models import StatementsResp, StatementType
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    NumPeriodsValidationMixin,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
    ValidQuarter,
)


class GetFinancialStatementFromIdentifiersArgs(ToolArgsWithIdentifiers, NumPeriodsValidationMixin):
    # no description because the description for enum fields comes from the enum docstring.
    statement: StatementType
    period_type: PeriodType | None = Field(default=None, description="The period type")
    start_year: int | None = Field(default=None, description="The starting year for the data range")
    end_year: int | None = Field(default=None, description="The ending year for the data range")
    start_quarter: ValidQuarter | None = Field(default=None, description="Starting quarter")
    end_quarter: ValidQuarter | None = Field(default=None, description="Ending quarter")
    calendar_type: CalendarType | None = Field(
        default=None, description="Fiscal year or calendar year"
    )
    num_periods: NumPeriods | None = Field(default=None)
    num_periods_back: NumPeriodsBack | None = Field(default=None)


class GetFinancialStatementFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, StatementsResp]  # company_id -> response


class GetFinancialStatementFromIdentifiers(KfinanceTool):
    name: str = "get_financial_statement_from_identifiers"
    description: str = dedent("""
        Get a financial statement associated with a group of identifiers.

        - To fetch the most recent value for the statement, leave start_year, start_quarter, end_year, and end_quarter as None.
        - The tool accepts arguments in calendar years, and all outputs will be presented in terms of calendar years. Please note that these calendar years may not align with the company's fiscal year.

        Example:
        Query: "Fetch the balance sheets of BAC and GS for 2024"
        Function: get_financial_statement_from_company_ids(identifiers=["BAC", "GS"], statement=StatementType.balance_sheet, start_year=2024, end_year=2024)
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
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)

        tasks = [
            Task(
                func=api_client.fetch_statement,
                kwargs=dict(
                    company_id=id_triple.company_id,
                    statement_type=statement.value,
                    period_type=period_type,
                    start_year=start_year,
                    end_year=end_year,
                    start_quarter=start_quarter,
                    end_quarter=end_quarter,
                    calendar_type=calendar_type,
                    num_periods=num_periods,
                    num_periods_back=num_periods_back,
                ),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]

        statement_responses: dict[str, StatementsResp] = process_tasks_in_thread_pool_executor(
            api_client=api_client, tasks=tasks
        )

        # If no date and multiple companies, only return the most recent value.
        # By default, we return 5 years of data, which can be too much when
        # returning data for many companies.
        if (
            start_year is None
            and end_year is None
            and start_quarter is None
            and end_quarter is None
            and len(statement_responses) > 1
        ):
            for statement_response in statement_responses.values():
                if statement_response.periods:
                    most_recent_year = max(statement_response.periods.keys())
                    most_recent_year_data = statement_response.periods[most_recent_year]
                    statement_response.periods = {most_recent_year: most_recent_year_data}

        return GetFinancialStatementFromIdentifiersResp(
            results=statement_responses, errors=list(id_triple_resp.errors.values())
        )
