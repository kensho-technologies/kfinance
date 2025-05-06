from typing import Type

from pydantic import BaseModel, Field

from kfinance.constants import Permission, YearAndQuarter
from kfinance.tool_calling.shared_models import KfinanceTool


class GetNQuartersAgoArgs(BaseModel):
    n: int = Field(description="Number of quarters before the current quarter")


class GetNQuartersAgo(KfinanceTool):
    name: str = "get_n_quarters_ago"
    description: str = (
        "Get the year and quarter corresponding to [n] quarters before the current quarter."
    )
    args_schema: Type[BaseModel] = GetNQuartersAgoArgs
    required_permission: Permission | None = None

    def _run(self, n: int) -> YearAndQuarter:
        return self.kfinance_client.get_n_quarters_ago(n)
