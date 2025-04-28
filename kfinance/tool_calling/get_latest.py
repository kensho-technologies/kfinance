from typing import Type

from pydantic import BaseModel, Field

from kfinance.constants import LatestPeriods, Permission
from kfinance.tool_calling.shared_models import KfinanceTool


class GetLatestArgs(BaseModel):
    use_local_timezone: bool = Field(
        description="Whether to use the local timezone of the user", default=True
    )


class GetLatest(KfinanceTool):
    name: str = "get_latest"
    description: str = "Get the latest annual reporting year, latest quarterly reporting quarter and year, and current date."
    args_schema: Type[BaseModel] = GetLatestArgs
    required_permission: Permission | None = None

    def _run(self, use_local_timezone: bool = True) -> LatestPeriods:
        return self.kfinance_client.get_latest(use_local_timezone=use_local_timezone)
