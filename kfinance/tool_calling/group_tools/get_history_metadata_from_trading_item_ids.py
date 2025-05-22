from textwrap import dedent
from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission, ToolMode
from kfinance.kfinance import TradingItem, TradingItems
from kfinance.tool_calling.shared_models import KfinanceTool


class GetHistoryMetadataFromTradingItemIdsArgs(BaseModel):
    trading_item_ids: list[int]


class GetHistoryMetadataFromTradingItemIds(KfinanceTool):
    name: str = "get_history_metadata_from_trading_item_ids"
    description: str = dedent("""
        Get the history metadata associated with a trading_item_id. History metadata includes currency, symbol, exchange name, instrument type, and first trade date.

        - When possible, pass multiple company_ids in a single call rather than making multiple calls.
    """).strip()
    args_schema: Type[BaseModel] = GetHistoryMetadataFromTradingItemIdsArgs
    required_permission: Permission | None = None
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(self, trading_item_ids: list[int]) -> dict[str, str | dict]:
        trading_items = TradingItems(
            kfinance_api_client=self.kfinance_client.kfinance_api_client,
            trading_item_ids=trading_item_ids,
        )
        fetched_results: dict[TradingItem, dict | None] = trading_items.history_metadata  # type:ignore[attr-defined]

        stringified_results = dict()
        for trading_item, result in fetched_results.items():
            stringified_result = "unavailable" if result is None else result
            stringified_results[f"trading_item_id: {trading_item.trading_item_id}"] = (
                stringified_result
            )

        return stringified_results
