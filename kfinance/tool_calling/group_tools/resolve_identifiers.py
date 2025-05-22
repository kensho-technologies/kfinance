from textwrap import dedent
from typing import Type

from pydantic import BaseModel, Field

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.constants import Permission, ToolMode
from kfinance.tool_calling.shared_models import KfinanceTool


class ResolveIdentifiersArgs(BaseModel):
    identifiers: list[str] = Field(
        description="A list of identifiers, which can be ticker symbols, ISINs, or CUSIPs"
    )


class ResolveIdentifiers(KfinanceTool):
    name: str = "resolve_identifiers"
    description: str = dedent("""
        Get the company_id, security_id, and trading_item_id associated with each identifier.

        - When possible, pass multiple company_ids in a single call rather than making multiple calls.

        Example:
        Query: What are the company_ids of AAPL and MSFT?
        Function: resolve_identifiers(identifiers=["AAPL", "MSFT"])
    """).strip()
    args_schema: Type[BaseModel] = ResolveIdentifiersArgs
    required_permission: Permission | None = None
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(self, identifiers: list[str]) -> dict[str, dict[str, int]]:
        """Return the company_id, security_id, and trading_item_id associated with each identifier.

        Example response:
        {"AAPL": {'company_id': 24937, 'security_id': 2590359, 'trading_item_id': 2590360}}
        """
        tasks = [
            Task(
                func=self.kfinance_client.kfinance_api_client.fetch_id_triple,
                args=(identifier,),
                result_key=identifier,
            )
            for identifier in identifiers
        ]
        id_triples_dict = process_tasks_in_thread_pool_executor(
            api_client=self.kfinance_client.kfinance_api_client, tasks=tasks
        )
        return id_triples_dict
