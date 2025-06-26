from textwrap import dedent
from typing import Literal, Type

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.constants import LINE_ITEM_NAMES_AND_ALIASES, PeriodType, Permission, ToolMode
from kfinance.tool_calling import GetFinancialLineItemFromIdentifiers
from kfinance.tool_calling.group_tools.company_identifiers import parse_identifiers
from kfinance.tool_calling.group_tools.identifier_resolvers import \
    fetch_company_ids_from_identifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifiers, ToolArgsWithIdentifier


class GetFinancialLineItemFromIdentifierArgs(ToolArgsWithIdentifier):
    # Note: mypy will not enforce this literal because of the type: ignore.
    # But pydantic still uses the literal to check for allowed values and only includes
    # allowed values in generated schemas.
    line_item: Literal[tuple(LINE_ITEM_NAMES_AND_ALIASES)] = Field(  # type: ignore[valid-type]
        description="The type of financial line_item requested"
    )
    period_type: PeriodType | None = Field(default=None, description="The period type")
    start_year: int | None = Field(default=None, description="The starting year for the data range")
    end_year: int | None = Field(default=None, description="The ending year for the data range")
    start_quarter: Literal[1, 2, 3, 4] | None = Field(default=None, description="Starting quarter")
    end_quarter: Literal[1, 2, 3, 4] | None = Field(default=None, description="Ending quarter")


class GetFinancialLineItemFromIdentifier(KfinanceTool):
    name: str = "get_financial_line_item_from_identifier"
    description: str = dedent("""
        Get the financial line item associated with an identifier.

        - To fetch the most recent value for the line item, leave start_year, start_quarter, end_year, and end_quarter as None.

        Example:
        Query: "What are the revenues of Lowe's?"
        Function: get_line_item(line_item="revenue", identifier="LW")
    """).strip()
    args_schema: Type[BaseModel] = GetFinancialLineItemFromIdentifierArgs
    required_permission: Permission | None = Permission.StatementsPermission
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(
        self,
        identifier: str,
        line_item: str,
        period_type: PeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
    ) -> dict[str, str]:
        group_tool = GetFinancialLineItemFromIdentifiers(kfinance_client=self.kfinance_client)
        return group_tool._run(
            identifiers=[identifier],
            line_item=line_item,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter
        )