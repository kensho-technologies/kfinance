from textwrap import dedent
from typing import Type

from pydantic import BaseModel

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.models.permission_models import Permission
from kfinance.tool_calling.company_identifiers import (
    fetch_trading_item_ids_from_identifiers,
    parse_identifiers,
)
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifiers


class GetHistoryMetadataFromIdentifiers(KfinanceTool):
    name: str = "get_history_metadata_from_identifiers"
    description: str = dedent("""
        Get the history metadata associated with a list of identifiers. History metadata includes currency, symbol, exchange name, instrument type, and first trade date.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = None

    def _run(self, identifiers: list[str]) -> dict:
        """Sample response:

        {
            'SPGI': {
                'currency': 'USD',
                'exchange_name': 'NYSE',
                'first_trade_date': '1968-01-02',
                'instrument_type': 'Equity',
                'symbol': 'SPGI'
            }
        }
        """
        parsed_identifiers = parse_identifiers(identifiers)
        identifiers_to_trading_item_ids = fetch_trading_item_ids_from_identifiers(
            identifiers=parsed_identifiers, api_client=self.kfinance_client.kfinance_api_client
        )

        tasks = [
            Task(
                func=self.kfinance_client.kfinance_api_client.fetch_history_metadata,
                kwargs=dict(trading_item_id=trading_item_id),
                result_key=identifier,
            )
            for identifier, trading_item_id in identifiers_to_trading_item_ids.items()
        ]

        history_metadata_responses = process_tasks_in_thread_pool_executor(
            api_client=self.kfinance_client.kfinance_api_client, tasks=tasks
        )

        return {
            str(identifier): result for identifier, result in history_metadata_responses.items()
        }
