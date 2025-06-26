from datetime import date
from textwrap import dedent
from typing import Type

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.constants import Capitalization, Permission, ToolMode
from kfinance.tool_calling import GetCapitalizationFromIdentifiers
from kfinance.tool_calling.group_tools.company_identifiers import parse_identifiers
from kfinance.tool_calling.group_tools.identifier_resolvers import \
    fetch_company_ids_from_identifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifiers, ToolArgsWithIdentifier


class GetCapitalizationFromIdentifierArgs(ToolArgsWithIdentifier):
    # no description because the description for enum fields comes from the enum docstring.
    capitalization: Capitalization
    start_date: date | None = Field(
        description="The start date for historical capitalization retrieval", default=None
    )
    end_date: date | None = Field(
        description="The end date for historical capitalization retrieval", default=None
    )


class GetCapitalizationFromIdentifier(KfinanceTool):
    name: str = "get_capitalization_from_identifier"
    description: str = dedent("""
        Get the historical market cap, tev (Total Enterprise Value), or shares outstanding for an identifier between inclusive start_date and inclusive end date.

        - When requesting the most recent values, leave start_date and end_date empty.

        Example:
        Query: "What is the market cap of AAPL?"
        Function: get_capitalization_from_identifiers(capitalization=Capitalization.market_cap, identifier="AAPL")
    """).strip()
    args_schema: Type[BaseModel] = GetCapitalizationFromIdentifierArgs
    required_permission: Permission | None = Permission.PricingPermission
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(
        self,
        identifier: str,
        capitalization: Capitalization,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:

        group_tool = GetCapitalizationFromIdentifiers(kfinance_client=self.kfinance_client)
        return group_tool._run(
            identifiers=[identifier],
            capitalization=capitalization,
            start_date=start_date,
            end_date=end_date
        )
