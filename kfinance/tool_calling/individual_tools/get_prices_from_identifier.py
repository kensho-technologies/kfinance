from datetime import date
from textwrap import dedent
from typing import Type

from pydantic import BaseModel, Field

from kfinance.constants import Periodicity, Permission, ToolMode
from kfinance.tool_calling import GetPricesFromIdentifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetPricesFromIdentifierArgs(ToolArgsWithIdentifier):
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


class GetPricesFromIdentifier(KfinanceTool):
    name: str = "get_prices_from_identifier"
    description: str = dedent("""
        Get the historical open, high, low, and close prices, and volume of an identifier between inclusive start_date and inclusive end date.

        - When requesting the most recent values, leave start_date and end_date empty.

        Example:
        Query: "What is the price of Facebook?"
        Function: get_prices_from_identifier(identifier="META")
    """).strip()
    args_schema: Type[BaseModel] = GetPricesFromIdentifierArgs
    required_permission: Permission | None = Permission.PricingPermission
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(
        self,
        identifier: str,
        start_date: date | None = None,
        end_date: date | None = None,
        periodicity: Periodicity = Periodicity.day,
        adjusted: bool = True,
    ) -> dict[str, str]:

        group_tool = GetPricesFromIdentifiers(kfinance_client=self.kfinance_client)
        return group_tool._run(identifiers=[identifier],
                               start_date=start_date,
                               end_date=end_date,
                               periodicity=periodicity,
                               adjusted=adjusted)
