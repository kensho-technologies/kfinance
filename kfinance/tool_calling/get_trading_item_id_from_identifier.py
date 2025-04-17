from typing import Type

from pydantic import BaseModel

from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetTradingItemIdFromIdentifier(KfinanceTool):
    name: str = "get_trading_item_id_from_identifier"
    description: str = "Get the trading item id associated with an identifier."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier

    def _run(self, identifier: str) -> int:
        return self.kfinance_client.ticker(identifier).trading_item_id
