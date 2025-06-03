from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission
from kfinance.kfinance import NoEarningsCallDataError
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetEarningsCalls(KfinanceTool):
    name: str = "get_earnings_calls"
    description: str = "Get all earnings calls for a given identifier."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = Permission.EarningsPermission

    def _run(self, identifier: str) -> list[dict]:
        ticker = self.kfinance_client.ticker(identifier)
        earnings_calls = ticker.company.earnings_calls()

        if not earnings_calls:
            raise NoEarningsCallDataError(f"Earnings calls for {identifier} not found")

        return [
            {
                "name": earnings_call.name,
                "key_dev_id": earnings_call.key_dev_id,
                "datetime": earnings_call.datetime.isoformat(),
            }
            for earnings_call in earnings_calls
        ]
