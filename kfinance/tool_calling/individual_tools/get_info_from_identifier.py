from textwrap import dedent
from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission, ToolMode
from kfinance.tool_calling import GetInfoFromIdentifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifiers


class GetInfoFromIdentifier(KfinanceTool):
    name: str = "get_info_from_identifier"
    description: str = dedent("""
        Get the information associated with an identifier. Info includes company name, status, type, simple industry, number of employees (if available), founding date, webpage, HQ address, HQ city, HQ zip code, HQ state, HQ country, and HQ country iso code.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    required_permission: Permission | None = None
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(self, identifier: str) -> dict[str, str | dict]:
        group_tool = GetInfoFromIdentifiers(kfinance_client=self.kfinance_client)
        return group_tool._run(identifiers=[identifier])
