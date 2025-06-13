from textwrap import dedent
from typing import Type

from pydantic import BaseModel

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.constants import Permission, ToolMode
from kfinance.tool_calling.group_tools.company_identifiers import parse_identifiers
from kfinance.tool_calling.group_tools.identifier_resolvers import \
    fetch_company_ids_from_identifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifiers


class GetInfoFromIdentifiers(KfinanceTool):
    name: str = "get_info_from_identifiers"
    description: str = dedent("""
        Get the information associated with a list of identifiers. Info includes company name, status, type, simple industry, number of employees (if available), founding date, webpage, HQ address, HQ city, HQ zip code, HQ state, HQ country, and HQ country iso code.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    required_permission: Permission | None = None
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(self, identifiers: list[str]) -> dict[str, str | dict]:
        parsed_identifiers = parse_identifiers(identifiers)
        identifiers_to_company_ids = fetch_company_ids_from_identifiers(
            identifiers=parsed_identifiers,
            api_client=self.kfinance_client.kfinance_api_client
        )

        tasks = [
            Task(
                func=self.kfinance_client.kfinance_api_client.fetch_info,
                kwargs=dict(company_id=company_id),
                result_key=identifier,
            )
            for identifier, company_id in identifiers_to_company_ids.items()
        ]

        info_responses = process_tasks_in_thread_pool_executor(
            api_client=self.kfinance_client.kfinance_api_client, tasks=tasks
        )

        return {str(id): result for id, result in info_responses.items()}