from typing import Type

from pydantic import BaseModel

from kfinance.constants import HistoryMetadata, Permission, ToolMode
from kfinance.tool_calling.shared_models import KfinanceTool


class GetHistoryMetadataFromTradingItemIdArgs(BaseModel):
    trading_item_id: int


class GetHistoryMetadataFromTradingItemId(KfinanceTool):
    name: str = "get_history_metadata_from_trading_item_id"
    description: str = "Get the history metadata associated with a trading_item_id. History metadata includes currency, symbol, exchange name, instrument type, and first trade date."
    args_schema: Type[BaseModel] = GetHistoryMetadataFromTradingItemIdArgs
    required_permission: Permission | None = None
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(self, trading_item_id: int) -> HistoryMetadata:
        return self.kfinance_client.trading_item(trading_item_id).history_metadata
