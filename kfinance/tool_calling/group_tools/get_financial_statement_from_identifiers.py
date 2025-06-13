from textwrap import dedent
from typing import Literal, Type

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.constants import PeriodType, Permission, StatementType, ToolMode
from kfinance.kfinance import Companies, Company
from kfinance.tool_calling.group_tools.company_identifiers import parse_identifiers
from kfinance.tool_calling.group_tools.identifier_resolvers import \
    fetch_company_ids_from_identifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifiers


class GetFinancialStatementFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    statement: StatementType
    period_type: PeriodType | None = Field(default=None, description="The period type")
    start_year: int | None = Field(default=None, description="The starting year for the data range")
    end_year: int | None = Field(default=None, description="The ending year for the data range")
    start_quarter: Literal[1, 2, 3, 4] | None = Field(default=None, description="Starting quarter")
    end_quarter: Literal[1, 2, 3, 4] | None = Field(default=None, description="Ending quarter")


class GetFinancialStatementFromIdentifiers(KfinanceTool):
    name: str = "get_financial_statement_from_identifiers"
    description: str = dedent("""
        Get a financial statement associated with a group of identifiers.

        - To fetch the most recent value for the statement, leave start_year, start_quarter, end_year, and end_quarter as None.

        Example:
        Query: "Fetch the balance sheets of BAC ash GS for 2024"
        Function: get_financial_statement_from_company_ids(identifiers=["BAC", "GS"], statement=StatementType.balance_sheet, start_year=2024, end_year=2024)
    """).strip()
    args_schema: Type[BaseModel] = GetFinancialStatementFromIdentifiersArgs
    required_permission: Permission | None = Permission.StatementsPermission
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(
        self,
        identifiers: list[str],
        statement: StatementType,
        period_type: PeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
    ) -> dict[str, str]:


        parsed_identifiers = parse_identifiers(identifiers)
        identifiers_to_company_ids = fetch_company_ids_from_identifiers(
            identifiers=parsed_identifiers, api_client=self.kfinance_client.kfinance_api_client
        )

        tasks = [
            Task(
                func=self.kfinance_client.kfinance_api_client.fetch_statement,
                kwargs=dict(
                    company_id=company_id,
                    statement_type=statement.value,
                    period_type=period_type,
                    start_year=start_year,
                    end_year=end_year,
                    start_quarter=start_quarter,
                    end_quarter=end_quarter
                ),
                result_key=identifier,
            )
            for identifier, company_id in identifiers_to_company_ids.items()
        ]

        statement_responses = process_tasks_in_thread_pool_executor(
            api_client=self.kfinance_client.kfinance_api_client, tasks=tasks
        )

        output = dict()
        for identifier, result in statement_responses.items():
            df = pd.DataFrame(result["statements"]).apply(pd.to_numeric).replace(np.nan, None).transpose()
            # If no date and multiple companies, only return the most recent value.
            if start_year == end_year == start_quarter == end_quarter and len(identifiers) > 1:
                df = df.tail(1)
            output[str(identifier)] = df.to_dict()

        return output

