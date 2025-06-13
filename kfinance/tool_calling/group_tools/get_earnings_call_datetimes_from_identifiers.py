from datetime import datetime
from textwrap import dedent
from typing import Type

from pydantic import BaseModel

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.constants import Permission, ToolMode
from kfinance.kfinance import Companies, Company
from kfinance.tool_calling.group_tools.company_identifiers import parse_identifiers
from kfinance.tool_calling.group_tools.identifier_resolvers import \
    fetch_company_ids_from_identifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifiers


class GetEarningsCallDatetimesFromIdentifiers(KfinanceTool):
    name: str = "get_earnings_call_datetimes_from_identifiers"
    description: str = dedent("""
        Get earnings call datetimes associated with a list of identifiers.

        - When possible, pass multiple company_ids in a single call rather than making multiple calls.

        Example:
        Query: "What were the earnings call datetimes of companies SPGI and TWSE:2353?"
        Function: get_earnings_call_datetimes_from_identifiers(identifiers=["SPGI", "TWSE:2353"])
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    required_permission: Permission | None = Permission.EarningsPermission
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(self, identifiers: list[str]) -> dict[str, list[str]]:

        parsed_identifiers = parse_identifiers(identifiers)
        identifiers_to_company_ids = fetch_company_ids_from_identifiers(
            identifiers=parsed_identifiers,
            api_client=self.kfinance_client.kfinance_api_client
        )

        tasks = [
            Task(
                func=self.kfinance_client.kfinance_api_client.fetch_earnings_dates,
                kwargs=dict(company_id=company_id),
                result_key=identifier,
            )
            for identifier, company_id in identifiers_to_company_ids.items()
        ]

        earnings_datetime_responses = process_tasks_in_thread_pool_executor(
            api_client=self.kfinance_client.kfinance_api_client, tasks=tasks
        )

        return {str(k): v["earnings"] for k, v in earnings_datetime_responses.items()}
