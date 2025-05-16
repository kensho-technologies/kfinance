from typing import Type

from pydantic import BaseModel, Field

from kfinance.constants import Permission, ToolMode
from kfinance.tool_calling.shared_models import KfinanceTool


class ResolveIdentifierArgs(BaseModel):
    identifier: str = Field(
        description="The identifier, which can be a ticker symbol, ISIN, or CUSIP"
    )


class ResolveIdentifier(KfinanceTool):
    name: str = "resolve_identifier"
    description: str = (
        "Get the company_id, security_id, and trading_item_id associated with an identifier."
    )
    args_schema: Type[BaseModel] = ResolveIdentifierArgs
    required_permission: Permission | None = None
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(self, identifier: str) -> dict[str, int]:
        return self.kfinance_client.ticker(identifier).id_triple._asdict()
