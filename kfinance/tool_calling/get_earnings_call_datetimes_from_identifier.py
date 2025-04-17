import json
from typing import Type

from pydantic import BaseModel

from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetEarningsCallDatetimesFromIdentifier(KfinanceTool):
    name: str = "get_earnings_call_datetimes_from_identifier"
    description: str = "Get earnings call datetimes associated with an identifier."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier

    def _run(self, identifier: str) -> str:
        ticker = self.kfinance_client.ticker(identifier)
        earnings_call_datetimes = ticker.earnings_call_datetimes
        return json.dumps([dt.isoformat() for dt in earnings_call_datetimes])
