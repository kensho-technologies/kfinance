from textwrap import dedent
from typing import Literal, Type

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.models.date_and_period_models import PeriodType
from kfinance.client.permission_models import Permission
from kfinance.domains.companies.company_identifiers import (
    Identifier,
    fetch_company_ids_from_identifiers,
    parse_identifiers,
)
from kfinance.domains.line_items.line_item_models import (
    LINE_ITEM_NAMES_AND_ALIASES,
    LineItemResponse,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
)


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
        Function: get_financial_line_item_from_identifiers(line_item="revenue", company_ids=["LW", "HD"])
    """).strip()
    args_schema: Type[BaseModel] = GetFinancialLineItemFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {
        Permission.StatementsPermission,
        Permission.PrivateCompanyFinancialsPermission,
    }

    def _run(
        self,
        identifiers: list[str],
        line_item: str,
        period_type: PeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
    ) -> dict:
        """Sample response:

        {
            'SPGI': {
                '2022': {'revenue': 11181000000.0},
                '2023': {'revenue': 12497000000.0},
                '2024': {'revenue': 14208000000.0}
            }
        }
        """
        api_client = self.kfinance_client.kfinance_api_client
        parsed_identifiers = parse_identifiers(identifiers=identifiers, api_client=api_client)
        identifiers_to_company_ids = fetch_company_ids_from_identifiers(
            identifiers=parsed_identifiers, api_client=api_client
        )

        tasks = [
            Task(
                func=api_client.fetch_line_item,
                kwargs=dict(
                    company_id=company_id,
                    line_item=line_item,
                    period_type=period_type,
                    start_year=start_year,
                    end_year=end_year,
                    start_quarter=start_quarter,
                    end_quarter=end_quarter,
                ),
                result_key=identifier,
            )
            for identifier, company_id in identifiers_to_company_ids.items()
        ]

        line_item_responses: dict[Identifier, LineItemResponse] = (
            process_tasks_in_thread_pool_executor(api_client=api_client, tasks=tasks)
        )

        output = dict()
        for identifier, result in line_item_responses.items():
            df = (
                pd.DataFrame({"line_item": result.line_item})
                .apply(pd.to_numeric)
                .replace(np.nan, None)
            )
            # If no date and multiple companies, only return the most recent value.
            # By default, we return 5 years of data, which can be too much when
            # returning data for many companies.
            if (
                start_year is None
                and end_year is None
                and start_quarter is None
                and end_quarter is None
                and len(identifiers) > 1
            ):
                df = df.tail(1)
            output[str(identifier)] = df.transpose().set_index(pd.Index([line_item])).to_dict()

        return output
