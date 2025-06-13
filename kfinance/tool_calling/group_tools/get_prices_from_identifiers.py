from datetime import date
from textwrap import dedent
from typing import Type

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.constants import Periodicity, Permission, ToolMode
from kfinance.kfinance import TradingItem, TradingItems
from kfinance.tool_calling.group_tools.company_identifiers import parse_identifiers
from kfinance.tool_calling.group_tools.identifier_resolvers import \
    fetch_trading_item_ids_from_identifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifiers


class GetPricesFromIdentifiersArgs(ToolArgsWithIdentifiers):
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


class GetPricesFromIdentifiers(KfinanceTool):
    name: str = "get_prices_from_identifiers"
    description: str = dedent("""
        Get the historical open, high, low, and close prices, and volume of a group of identifiers between inclusive start_date and inclusive end date.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - When requesting the most recent values, leave start_date and end_date empty.

        Example:
        Query: "What are the prices of Facebook and Google?"
        Do:
            get_prices_from_identifiers(identifiers=["META", "GOOGL"])
        Don't:
            get_prices_from_identifiers(trading_item_ids=["META"])
            get_prices_from_identifiers(trading_item_ids=["GOOGL"])
    """).strip()
    args_schema: Type[BaseModel] = GetPricesFromIdentifiersArgs
    required_permission: Permission | None = Permission.PricingPermission
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(
        self,
        identifiers: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
        periodicity: Periodicity = Periodicity.day,
        adjusted: bool = True,
    ) -> dict[str, str]:

        parsed_identifiers = parse_identifiers(identifiers)
        identifiers_to_trading_item_ids = fetch_trading_item_ids_from_identifiers(
            identifiers=parsed_identifiers, api_client=self.kfinance_client.kfinance_api_client
        )

        tasks = [
            Task(
                func=self.kfinance_client.kfinance_api_client.fetch_history,
                kwargs=dict(
                    trading_item_id=trading_item_id,
                    start_date=start_date,
                    end_date=end_date,
                    periodicity=periodicity,
                    is_adjusted=adjusted
                ),
                result_key=identifier,
            )
            for identifier, trading_item_id in identifiers_to_trading_item_ids.items()
        ]

        price_responses = process_tasks_in_thread_pool_executor(
            api_client=self.kfinance_client.kfinance_api_client, tasks=tasks
        )

        output = dict()
        for identifier, result in price_responses.items():
            df = pd.DataFrame(result["prices"]).set_index("date").apply(pd.to_numeric).replace(np.nan, None)
            # If more than one identifier was passed without start and end date,
            # assume that the caller only cares about the last known value
            if (
                start_date == end_date is None
                and len(identifiers) > 1
                and df["close"].iloc[-1] is not None
            ):
                df = df.tail(1)
            output[str(identifier)] = df.to_dict(orient="index")

        return output