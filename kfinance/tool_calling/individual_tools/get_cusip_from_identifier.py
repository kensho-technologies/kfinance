from typing import Type

from pydantic import BaseModel

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.constants import Permission, ToolMode
from kfinance.kfinance import Securities, Security
from kfinance.tool_calling.group_tools.company_identifiers import parse_identifiers
from kfinance.tool_calling.group_tools.identifier_resolvers import \
    fetch_security_ids_from_identifiers
from kfinance.tool_calling.group_tools.get_cusip_from_identifiers import GetCusipFromIdentifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifiers, ToolArgsWithIdentifier


class GetCusipFromIdentifier(KfinanceTool):
    name: str = "get_cusip_from_identifier"
    description: str = "Get the CUSIP for an identifier."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = Permission.IDPermission
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(self, identifier: str) -> dict[str, str]:

        group_tool = GetCusipFromIdentifiers(kfinance_client=self.kfinance_client)
        return group_tool._run(identifiers=[identifier])
