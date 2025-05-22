from datetime import date
from textwrap import dedent
from typing import Type

import pandas as pd
from pydantic import BaseModel, Field

from kfinance.constants import Periodicity, Permission, ToolMode
from kfinance.kfinance import TradingItem, TradingItems
from kfinance.tool_calling.shared_models import KfinanceTool


class GetPricesFromTradingItemIdsArgs(BaseModel):
    trading_item_ids: list[int]
    start_date: date | None = Field(
        description="The start date for historical price retrieval", default=None
    )
    end_date: date | None = Field(
        description="The end date for historical price retrieval", default=None
    )
    # no description because the description for enum fields comes from the enum docstring.
    periodicity: Periodicity = Field(default=Periodicity.day)
    adjusted: bool = Field(
        description="Whether to retrieve adjusted prices that account for corporate actions such as dividends and splits.",
        default=True,
    )


class GetPricesFromTradingItemIds(KfinanceTool):
    name: str = "get_prices_from_trading_item_ids"
    description: str = dedent("""
        Get the historical open, high, low, and close prices, and volume of a group of trading_item_ids between inclusive start_date and inclusive end date.

        - When possible, pass multiple trading_item_ids in a single call rather than making multiple calls.
        - When requesting the most recent values, leave start_date and end_date empty.

        Example:
        Query: "What are the prices of trading_item_ids 2630413 and 2590360?"
        Do:
            get_prices_from_trading_item_ids(trading_item_ids=[2630413, 2590360])
        Don't:
            get_prices_from_trading_item_ids(trading_item_ids=[2630413])
            get_prices_from_trading_item_ids(trading_item_ids=[2590360])
    """).strip()
    args_schema: Type[BaseModel] = GetPricesFromTradingItemIdsArgs
    required_permission: Permission | None = Permission.PricingPermission
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(
        self,
        trading_item_ids: list[int],
        start_date: date | None = None,
        end_date: date | None = None,
        periodicity: Periodicity = Periodicity.day,
        adjusted: bool = True,
    ) -> dict[str, str]:
        trading_items = TradingItems(
            kfinance_api_client=self.kfinance_client.kfinance_api_client,
            trading_item_ids=trading_item_ids,
        )
        fetched_results: dict[TradingItem, pd.DataFrame | None] = trading_items.history(  # type:ignore[attr-defined]
            start_date=start_date.isoformat() if start_date else None,
            end_date=end_date.isoformat() if end_date else None,
            periodicity=periodicity,
            adjusted=adjusted,
        )

        stringified_results = dict()
        for trading_item, result in fetched_results.items():
            if result is None:
                stringified_result = "unavailable"
            elif (
                start_date == end_date is None
                and len(trading_item_ids) > 1
                and result["close"].iloc[-1] is not None
            ):
                # If more than one trading item was passed without start and end date,
                # assume that the caller only cares about the last known value
                stringified_result = str(result.tail(1).to_dict(orient="index"))
            else:
                stringified_result = result.to_markdown()
            stringified_results[f"trading_item_id: {trading_item.trading_item_id}"] = (
                stringified_result
            )
        return stringified_results
