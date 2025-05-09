from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class ResolveIdentifier(KfinanceTool):
    name: str = "resolve_identifier"
    description: str = (
        "Get the company_id, security_id, and trading_item_id associated with an identifier."
    )
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = None

    def _run(self, identifier: str) -> dict[str, int]:
        return self.kfinance_client.ticker(identifier).id_triple._asdict()
