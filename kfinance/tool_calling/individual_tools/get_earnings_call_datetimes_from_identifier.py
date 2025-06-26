from textwrap import dedent
from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission, ToolMode
from kfinance.tool_calling import GetEarningsCallDatetimesFromIdentifiers

from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetEarningsCallDatetimesFromIdentifier(KfinanceTool):
    name: str = "get_earnings_call_datetimes_from_identifier"
    description: str = dedent("""
        Get earnings call datetimes associated with an identifier.

        Example:
        Query: "What were the earnings call datetimes of SPGI?"
        Function: get_earnings_call_datetimes_from_identifiers(identifier="SPGI")
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = Permission.EarningsPermission
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(self, identifier: str) -> dict[str, list[str]]:
        group_tool = GetEarningsCallDatetimesFromIdentifiers(kfinance_client=self.kfinance_client)
        return group_tool._run(identifiers=[identifier])
