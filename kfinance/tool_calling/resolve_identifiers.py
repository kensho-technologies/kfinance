from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class ResolveIdentifiers(KfinanceTool):
    name: str = "resolve_identifiers"
    description: str = (
        "Get the company id, security id, and trading item id associated with an identifier."
    )
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = None

    def _run(self, identifier: str) -> dict[str, int]:
        return self.kfinance_client.ticker(identifier).id_triple._asdict()
