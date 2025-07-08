from typing import Type

from pydantic import BaseModel

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.models.permission_models import Permission
from kfinance.tool_calling.company_identifiers import (
    fetch_security_ids_from_identifiers,
    parse_identifiers,
)
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifiers


class GetIsinFromSecurityIdsArgs(BaseModel):
    security_ids: list[int]


class GetIsinFromIdentifiers(KfinanceTool):
    name: str = "get_isin_from_identifiers"
    description: str = "Get the ISINs for a group of identifiers."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.IDPermission}

    def _run(self, identifiers: list[str]) -> dict:
        """Sample response:

        {"SPGI": "US78409V1044"}
        """

        parsed_identifiers = parse_identifiers(identifiers)
        identifiers_to_security_ids = fetch_security_ids_from_identifiers(
            identifiers=parsed_identifiers, api_client=self.kfinance_client.kfinance_api_client
        )

        tasks = [
            Task(
                func=self.kfinance_client.kfinance_api_client.fetch_isin,
                kwargs=dict(security_id=security_id),
                result_key=identifier,
            )
            for identifier, security_id in identifiers_to_security_ids.items()
        ]

        isin_responses = process_tasks_in_thread_pool_executor(
            api_client=self.kfinance_client.kfinance_api_client, tasks=tasks
        )

        return {str(identifier): resp["isin"] for identifier, resp in isin_responses.items()}
