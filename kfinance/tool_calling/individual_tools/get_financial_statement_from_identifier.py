from textwrap import dedent
from typing import Literal, Type

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.constants import PeriodType, Permission, StatementType, ToolMode
from kfinance.kfinance import Companies, Company
from kfinance.tool_calling import GetFinancialStatementFromIdentifiers
from kfinance.tool_calling.group_tools.company_identifiers import parse_identifiers
from kfinance.tool_calling.group_tools.identifier_resolvers import \
    fetch_company_ids_from_identifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifiers, ToolArgsWithIdentifier


class GetFinancialStatementFromIdentifierArgs(ToolArgsWithIdentifier):
    # no description because the description for enum fields comes from the enum docstring.
    statement: StatementType
    period_type: PeriodType | None = Field(default=None, description="The period type")
    start_year: int | None = Field(default=None, description="The starting year for the data range")
    end_year: int | None = Field(default=None, description="The ending year for the data range")
    start_quarter: Literal[1, 2, 3, 4] | None = Field(default=None, description="Starting quarter")
    end_quarter: Literal[1, 2, 3, 4] | None = Field(default=None, description="Ending quarter")


class GetFinancialStatementFromIdentifier(KfinanceTool):
    name: str = "get_financial_statement_from_identifier"
    description: str = dedent("""
        Get a financial statement associated with an identifier.

        - To fetch the most recent value for the statement, leave start_year, start_quarter, end_year, and end_quarter as None.

        Example:
        Query: "Fetch the balance sheets of BAC for 2024"
        Function: get_financial_statement_from_company_ids(identifier="BAC", statement=StatementType.balance_sheet, start_year=2024, end_year=2024)
    """).strip()
    args_schema: Type[BaseModel] = GetFinancialStatementFromIdentifierArgs
    required_permission: Permission | None = Permission.StatementsPermission
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(
        self,
        identifier: str,
        statement: StatementType,
        period_type: PeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
    ) -> dict[str, str]:

        group_tool = GetFinancialStatementFromIdentifiers(kfinance_client=self.kfinance_client)
        return group_tool._run(
            identifiers=[identifier],
            statement=statement,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter
        )
