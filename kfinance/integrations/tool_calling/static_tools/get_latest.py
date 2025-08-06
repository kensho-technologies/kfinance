from typing import Type

from pydantic import BaseModel, Field

from kfinance.client.models.date_and_period_models import LatestPeriods
from kfinance.client.permission_models import Permission
from kfinance.integrations.tool_calling.tool_calling_models import KfinanceTool


class GetLatestArgs(BaseModel):
    use_local_timezone: bool = Field(
        description="Whether to use the local timezone of the user", default=True
    )


class GetLatest(KfinanceTool):
    name: str = "get_latest"
    description: str = "Get the latest annual reporting year, latest quarterly reporting quarter and year, and current date."
    args_schema: Type[BaseModel] = GetLatestArgs
    accepted_permissions: set[Permission] | None = None

    def _run(self, use_local_timezone: bool = True) -> LatestPeriods:
        return self.kfinance_client.get_latest(use_local_timezone=use_local_timezone)
