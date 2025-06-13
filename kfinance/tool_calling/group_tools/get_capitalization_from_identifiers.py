from datetime import date
from textwrap import dedent
from typing import Type

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.constants import Capitalization, Permission, ToolMode
from kfinance.tool_calling.group_tools.company_identifiers import parse_identifiers
from kfinance.tool_calling.group_tools.identifier_resolvers import \
    fetch_company_ids_from_identifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifiers


class GetCapitalizationFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    capitalization: Capitalization
    start_date: date | None = Field(
        description="The start date for historical capitalization retrieval", default=None
    )
    end_date: date | None = Field(
        description="The end date for historical capitalization retrieval", default=None
    )


class GetCapitalizationFromIdentifiers(KfinanceTool):
    name: str = "get_capitalization_from_identifiers"
    description: str = dedent("""
        Get the historical market cap, tev (Total Enterprise Value), or shares outstanding for a group of identifiers between inclusive start_date and inclusive end date.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - When requesting the most recent values, leave start_date and end_date empty.

        Example:
        Query: "What are the market caps of AAPL and WMT?"
        Function: get_capitalization_from_identifiers(capitalization=Capitalization.market_cap, identifiers=["AAPL", "WMT"])
    """).strip()
    args_schema: Type[BaseModel] = GetCapitalizationFromIdentifiersArgs
    required_permission: Permission | None = Permission.PricingPermission
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(
        self,
        identifiers: list[str],
        capitalization: Capitalization,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:

        parsed_identifiers = parse_identifiers(identifiers)
        identifiers_to_company_ids = fetch_company_ids_from_identifiers(
            identifiers=parsed_identifiers, api_client=self.kfinance_client.kfinance_api_client
        )

        tasks = [
            Task(
                func=self.kfinance_client.kfinance_api_client.fetch_market_caps_tevs_and_shares_outstanding,
                kwargs=dict(
                    company_id=company_id,
                    start_date=start_date,
                    end_date=end_date
                ),
                result_key=identifier,
            )
            for identifier, company_id in identifiers_to_company_ids.items()
        ]

        capitalization_responses = process_tasks_in_thread_pool_executor(
            api_client=self.kfinance_client.kfinance_api_client, tasks=tasks
        )


        output = dict()
        for identifier, result in capitalization_responses.items():
            df = pd.DataFrame(result["market_caps"]).set_index("date")[[capitalization.value]].apply(pd.to_numeric).replace(np.nan, None)
            if start_date == end_date is None and len(identifiers) > 1:
                # If more than one company was passed without start and end date,
                # assume that the caller only cares about the last known value
                df = df.tail(1)

            output[str(identifier)] = df.to_dict()
        return output
