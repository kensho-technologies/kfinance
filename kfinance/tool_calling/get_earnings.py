from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission
from kfinance.kfinance import NoEarningsDataError
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetEarnings(KfinanceTool):
    name: str = "get_earnings"
    description: str = "Get all earnings for a given identifier. Returns a list of dictionaries, each with 'name' (str), 'key_dev_id' (int), and 'datetime' (str in ISO 8601 format with UTC timezone) attributes."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = Permission.EarningsPermission

    def _run(self, identifier: str) -> list[dict]:
        ticker = self.kfinance_client.ticker(identifier)
        earnings = ticker.company.earnings()

        if not earnings:
            raise NoEarningsDataError(f"Earnings for {identifier} not found")

        return [
            {
                "name": earnings_item.name,
                "key_dev_id": earnings_item.key_dev_id,
                "datetime": earnings_item.datetime.isoformat(),
            }
            for earnings_item in earnings
        ]
