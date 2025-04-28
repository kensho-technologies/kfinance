from typing import Type

from pydantic import BaseModel, Field

from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool


class GetIsinFromTickerArgs(BaseModel):
    ticker_str: str = Field(description="The ticker")


class GetIsinFromTicker(KfinanceTool):
    name: str = "get_isin_from_ticker"
    description: str = "Get the ISIN associated with a ticker."
    args_schema: Type[BaseModel] = GetIsinFromTickerArgs
    required_permission: Permission | None = Permission.IDPermission

    def _run(self, ticker_str: str) -> str:
        return self.kfinance_client.ticker(ticker_str).isin
