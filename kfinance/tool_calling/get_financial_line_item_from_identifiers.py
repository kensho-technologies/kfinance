from textwrap import dedent
from typing import Literal, Type

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.constants import LINE_ITEM_NAMES_AND_ALIASES, PeriodType, Permission, ToolMode
from kfinance.tool_calling.company_identifiers import parse_identifiers, fetch_company_ids_from_identifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifiers


class GetFinancialLineItemFromIdentifiersArgs(ToolArgsWithIdentifiers):
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


class GetFinancialLineItemFromIdentifiers(KfinanceTool):
    name: str = "get_financial_line_item_from_identifiers"
    description: str = dedent("""
        Get the financial line item associated with a list of identifiers.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - To fetch the most recent value for the line item, leave start_year, start_quarter, end_year, and end_quarter as None.

        Example:
        Query: "What are the revenues of Lowe's and Home Depot?"
        Function: get_line_item(line_item="revenue", company_ids=["LW", "HD"])
    """).strip()
    args_schema: Type[BaseModel] = GetFinancialLineItemFromIdentifiersArgs
    required_permission: Permission | None = Permission.StatementsPermission
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(
        self,
        identifiers: list[str],
        line_item: str,
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
                func=self.kfinance_client.kfinance_api_client.fetch_line_item,
                kwargs=dict(
                    company_id=company_id,
                    line_item=line_item,
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

        line_item_responses = process_tasks_in_thread_pool_executor(
            api_client=self.kfinance_client.kfinance_api_client, tasks=tasks
        )

        output = dict()
        for identifier, result in line_item_responses.items():
            df = pd.DataFrame(result).apply(pd.to_numeric).replace(np.nan, None)
            # If no date and multiple companies, only return the most recent value.
            if start_year == end_year == start_quarter == end_quarter and len(identifiers) > 1:
                df = df.tail(1)
            output[str(identifier)] = df.transpose().set_index(pd.Index([line_item])).to_dict()

        return output
