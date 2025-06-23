from typing import Literal, Type

from pydantic import BaseModel, Field

from kfinance.constants import PeriodType, Permission, SegmentType
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier, ValidQuarter


class GetSegmentsFromIdentifierArgs(ToolArgsWithIdentifier):
    # no description because the description for enum fields comes from the enum docstring.
    segment_type: SegmentType
    period_type: PeriodType | None = Field(default=None, description="The period type")
    start_year: int | None = Field(default=None, description="The starting year for the data range")
    end_year: int | None = Field(default=None, description="The ending year for the data range")
    start_quarter: ValidQuarter | None = Field(default=None, description="Starting quarter")
    end_quarter: ValidQuarter | None = Field(default=None, description="Ending quarter")


class GetSegmentsFromIdentifier(KfinanceTool):
    name: str = "get_segments_from_identifier"
    description: str = "Get the templated segments associated with an identifier."
    args_schema: Type[BaseModel] = GetSegmentsFromIdentifierArgs
    required_permission: Permission | None = Permission.SegmentsPermission

    def _run(
        self,
        identifier: str,
        segment_type: SegmentType,
        period_type: PeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
    ) -> str:
        ticker = self.kfinance_client.ticker(identifier)
        return getattr(ticker, segment_type.value + "_segments")(
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )
