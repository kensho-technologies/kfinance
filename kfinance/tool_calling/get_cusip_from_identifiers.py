from typing import Type

from pydantic import BaseModel

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.constants import Permission, ToolMode
from kfinance.tool_calling.company_identifiers import parse_identifiers, fetch_security_ids_from_identifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifiers


class GetCusipFromIdentifiers(KfinanceTool):
    name: str = "get_cusip_from_identifiers"
    description: str = "Get the CUSIPs for a group of identifiers."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    required_permission: Permission | None = Permission.IDPermission
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(self, identifiers: list[str]) -> dict[str, str]:

        parsed_identifiers = parse_identifiers(identifiers)
        identifiers_to_security_ids = fetch_security_ids_from_identifiers(
            identifiers=parsed_identifiers, api_client=self.kfinance_client.kfinance_api_client
        )

        tasks = [
            Task(
                func=self.kfinance_client.kfinance_api_client.fetch_cusip,
                kwargs=dict(security_id=security_id),
                result_key=identifier,
            )
            for identifier, security_id in identifiers_to_security_ids.items()
        ]

        cusip_responses = process_tasks_in_thread_pool_executor(
            api_client=self.kfinance_client.kfinance_api_client, tasks=tasks
        )

        return {
            str(identifier): resp["cusip"] for identifier, resp in cusip_responses.items()
        }