from textwrap import dedent
from typing import Type

from pydantic import BaseModel

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.kfinance import NoEarningsDataError
from kfinance.models.permission_models import Permission
from kfinance.tool_calling.company_identifiers import parse_identifiers, fetch_company_ids_from_identifiers
from kfinance.tool_calling.earnings.earnings_helpers import get_earnings_from_identifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier, ToolArgsWithIdentifiers


class GetEarningsFromIdentifiers(KfinanceTool):
    name: str = "get_earnings_from_identifiers"
    description: str = dedent("""
        Get all earnings for a list of identifiers. 
        
        Returns a list of dictionaries, each with 'name' (str), 'key_dev_id' (int), and 'datetime' (str in ISO 8601 format with UTC timezone) attributes.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {
        Permission.EarningsPermission,
        Permission.TranscriptsPermission,
    }

    def _run(self, identifiers: list[str]) -> dict:
        """
        Sample response:

        {
            'SPGI': [
                {
                    'datetime': '2025-04-29T12:30:00Z',
                    'key_dev_id': 12346,
                    'name': 'SPGI Q1 2025 Earnings Call'
                }
            ]
        }

        """
        earnings_responses = get_earnings_from_identifiers(
            identifiers=identifiers, kfinance_api_client=self.kfinance_client.kfinance_api_client
        )
        return {str(identifier): earnings["earnings"] for identifier, earnings in earnings_responses.items()}
