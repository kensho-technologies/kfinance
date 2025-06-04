from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission
from kfinance.kfinance import NoEarningsDataError
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetNextEarnings(KfinanceTool):
    name: str = "get_next_earnings"
    description: str = "Get the next earnings for a given identifier. Returns a dictionary with 'name' (str), 'key_dev_id' (int), and 'datetime' (str in ISO 8601 format with UTC timezone) attributes."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = Permission.EarningsPermission

    def _run(self, identifier: str) -> dict:
        ticker = self.kfinance_client.ticker(identifier)
        next_earnings = ticker.company.next_earnings

        if next_earnings is None:
            raise NoEarningsDataError(f"Next earnings for {identifier} not found")

        return {
            "name": next_earnings.name,
            "key_dev_id": next_earnings.key_dev_id,
            "datetime": next_earnings.datetime.isoformat(),
        }
