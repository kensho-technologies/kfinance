from textwrap import dedent
from typing import Type

from pydantic import BaseModel

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.constants import Permission, ToolMode
from kfinance.tool_calling import GetHistoryMetadataFromIdentifiers
from kfinance.tool_calling.group_tools.company_identifiers import parse_identifiers
from kfinance.tool_calling.group_tools.identifier_resolvers import \
    fetch_trading_item_ids_from_identifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifiers, ToolArgsWithIdentifier


class GetHistoryMetadataFromIdentifier(KfinanceTool):
    name: str = "get_history_metadata_from_identifier"
    description: str = dedent("""
        Get the history metadata associated with an identifier. History metadata includes currency, symbol, exchange name, instrument type, and first trade date.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = None
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(self, identifier: str) -> dict[str, str | dict]:

        group_tool = GetHistoryMetadataFromIdentifiers(kfinance_client=self.kfinance_client)
        return group_tool._run(identifiers=[identifier])
