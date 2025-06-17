from typing import Literal, Type

from pydantic import BaseModel, Field

from kfinance.constants import LINE_ITEM_NAMES_AND_ALIASES, PeriodType, Permission
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier, ValidQuarter


class GetFinancialLineItemFromIdentifierArgs(ToolArgsWithIdentifier):
    # Note: mypy will not enforce this literal because of the type: ignore.
    # But pydantic still uses the literal to check for allowed values and only includes
    # allowed values in generated schemas.
    line_item: Literal[tuple(LINE_ITEM_NAMES_AND_ALIASES)] = Field(  # type: ignore[valid-type]
        description="The type of financial line_item requested"
    )
    period_type: PeriodType | None = Field(default=None, description="The period type")
    start_year: int | None = Field(default=None, description="The starting year for the data range")
    end_year: int | None = Field(default=None, description="The ending year for the data range")
    start_quarter: ValidQuarter | None = Field(default=None, description="Starting quarter")
    end_quarter: ValidQuarter | None = Field(default=None, description="Ending quarter")


class GetFinancialLineItemFromIdentifier(KfinanceTool):
    name: str = "get_financial_line_item_from_identifier"
    description: str = "Get the financial line item associated with an identifier."
    args_schema: Type[BaseModel] = GetFinancialLineItemFromIdentifierArgs
    required_permission: Permission | None = Permission.StatementsPermission

    def _run(
        self,
        identifier: str,
        line_item: str,
        period_type: PeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
    ) -> str:
        ticker = self.kfinance_client.ticker(identifier)
        return getattr(ticker, line_item)(
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        ).to_markdown()
