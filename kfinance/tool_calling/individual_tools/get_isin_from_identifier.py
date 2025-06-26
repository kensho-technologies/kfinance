from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission, ToolMode
from kfinance.tool_calling import GetIsinFromIdentifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetIsinFromIdentifier(KfinanceTool):
    name: str = "get_isin_from_identifier"
    description: str = "Get the ISINs for an identifier."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = Permission.IDPermission
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(self, identifier: str) -> dict[str, str]:
        group_tool = GetIsinFromIdentifiers(kfinance_client=self.kfinance_client)
        return group_tool._run(identifiers=[identifier])
