from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission
from kfinance.kfinance import NoEarningsCallDataError
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetLatestEarningsCall(KfinanceTool):
    name: str = "get_latest_earnings_call"
    description: str = "Get the latest earnings call for a given identifier. Returns a dictionary with 'name' (str), 'key_dev_id' (int), and 'datetime' (str in ISO 8601 format with UTC timezone) attributes."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = Permission.EarningsPermission

    def _run(self, identifier: str) -> dict:
        ticker = self.kfinance_client.ticker(identifier)
        latest_earnings_call = ticker.company.last_earnings_call

        if latest_earnings_call is None:
            raise NoEarningsCallDataError(f"Latest earnings call for {identifier} not found")

        return {
            "name": latest_earnings_call.name,
            "key_dev_id": latest_earnings_call.key_dev_id,
            "datetime": latest_earnings_call.datetime.isoformat(),
        }
