from textwrap import dedent
from typing import Literal, Type

from pydantic import BaseModel, Field

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.models.date_and_period_models import PeriodType
from kfinance.client.permission_models import Permission
from kfinance.domains.line_items.line_item_models import (
    LINE_ITEM_NAMES_AND_ALIASES,
    LineItemResponse,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
    ValidQuarter,
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
    start_quarter: ValidQuarter | None = Field(default=None, description="Starting quarter")
    end_quarter: ValidQuarter | None = Field(default=None, description="Ending quarter")


class GetFinancialLineItemFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, LineItemResponse]


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
    ) -> GetFinancialLineItemFromIdentifiersResp:
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
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)

        tasks = [
            Task(
                func=api_client.fetch_line_item,
                kwargs=dict(
                    company_id=id_triple.company_id,
                    line_item=line_item,
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

        line_item_responses: dict[str, LineItemResponse] = process_tasks_in_thread_pool_executor(
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
            and len(line_item_responses) > 1
        ):
            for line_item_response in line_item_responses.values():
                most_recent_year = max(line_item_response.line_item.keys())
                most_recent_year_data = line_item_response.line_item[most_recent_year]
                line_item_response.line_item = {most_recent_year: most_recent_year_data}

        return GetFinancialLineItemFromIdentifiersResp(
            results=line_item_responses, errors=list(id_triple_resp.errors.values())
        )
