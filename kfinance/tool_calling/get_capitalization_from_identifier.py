from datetime import date

from pydantic import Field

from kfinance.constants import Capitalization, Permission
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


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
    description: str = "Get the historical market cap, tev (Total Enterprise Value), or shares outstanding of an identifier between inclusive start_date and inclusive end date. When requesting the most recent values, leave start_date and end_date empty."
    args_schema = GetCapitalizationFromIdentifierArgs
    required_permission: Permission | None = Permission.PricingPermission

    def _run(
        self,
        identifier: str,
        capitalization: Capitalization,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        ticker = self.kfinance_client.ticker(identifier)
        return getattr(ticker, capitalization.value)(
            start_date=start_date, end_date=end_date
        ).to_markdown()
