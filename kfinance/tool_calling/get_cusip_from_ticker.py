from typing import Type

from pydantic import BaseModel, Field

from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool


class GetCusipFromTickerArgs(BaseModel):
    ticker_str: str = Field(description="The ticker")


class GetCusipFromTicker(KfinanceTool):
    name: str = "get_cusip_from_ticker"
    description: str = "Get the CUSIP associated with a ticker."
    args_schema: Type[BaseModel] = GetCusipFromTickerArgs
    required_permission: Permission | None = Permission.IDPermission

    def _run(self, ticker_str: str) -> str:
        return self.kfinance_client.ticker(ticker_str).cusip
