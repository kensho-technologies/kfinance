from typing import Type

from pydantic import BaseModel, Field

from kfinance.client.models.date_and_period_models import YearAndQuarter
from kfinance.client.permission_models import Permission
from kfinance.integrations.tool_calling.tool_calling_models import KfinanceTool


class GetNQuartersAgoArgs(BaseModel):
    n: int = Field(description="Number of quarters before the current quarter")


class GetNQuartersAgo(KfinanceTool):
    name: str = "get_n_quarters_ago"
    description: str = (
        "Get the year and quarter corresponding to [n] quarters before the current quarter."
    )
    args_schema: Type[BaseModel] = GetNQuartersAgoArgs
    accepted_permissions: set[Permission] | None = None

    def _run(self, n: int) -> YearAndQuarter:
        return self.kfinance_client.get_n_quarters_ago(n)
