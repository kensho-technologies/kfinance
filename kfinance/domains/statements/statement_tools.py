from textwrap import dedent
from typing import Literal, Type

from pydantic import BaseModel, Field

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.models.date_and_period_models import PeriodType
from kfinance.client.permission_models import Permission
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
    period_type: PeriodType | None = Field(default=None, description="The period type")
    start_year: int | None = Field(default=None, description="The starting year for the data range")
    end_year: int | None = Field(default=None, description="The ending year for the data range")
    start_quarter: ValidQuarter | None = Field(default=None, description="Starting quarter")
    end_quarter: ValidQuarter | None = Field(default=None, description="Ending quarter")


class GetFinancialStatementFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, StatementsResp]


class GetFinancialStatementFromIdentifiers(KfinanceTool):
    name: str = "get_financial_statement_from_identifiers"
    description: str = dedent("""
        Get a financial statement associated with a group of identifiers.

        - To fetch the most recent value for the statement, leave start_year, start_quarter, end_year, and end_quarter as None.

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
    ) -> GetFinancialStatementFromIdentifiersResp:
        """Sample response:

        {
            'results': {
                'SPGI': {
                    'statements': {
                        '2020': {'Revenues': '7442000000.000000', 'Total Revenues': '7442000000.000000'},
                        '2021': {'Revenues': '8243000000.000000', 'Total Revenues': '8243000000.000000'}
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
                if statement_response.statements:
                    most_recent_year = max(statement_response.statements.keys())
                    most_recent_year_data = statement_response.statements[most_recent_year]
                    statement_response.statements = {most_recent_year: most_recent_year_data}

        return GetFinancialStatementFromIdentifiersResp(
            results=statement_responses, errors=list(id_triple_resp.errors.values())
        )
