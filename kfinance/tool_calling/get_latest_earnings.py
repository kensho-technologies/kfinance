from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission
from kfinance.kfinance import NoEarningsDataError
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetLatestEarnings(KfinanceTool):
    name: str = "get_latest_earnings"
    description: str = "Get the latest earnings for a given identifier. Returns a dictionary with 'name' (str), 'key_dev_id' (int), and 'datetime' (str in ISO 8601 format with UTC timezone) attributes."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = Permission.EarningsPermission

    def _run(self, identifier: str) -> dict:
        ticker = self.kfinance_client.ticker(identifier)
        latest_earnings = ticker.company.latest_earnings

        if latest_earnings is None:
            raise NoEarningsDataError(f"Latest earnings for {identifier} not found")

        return {
            "name": latest_earnings.name,
            "key_dev_id": latest_earnings.key_dev_id,
            "datetime": latest_earnings.datetime.isoformat(),
        }
