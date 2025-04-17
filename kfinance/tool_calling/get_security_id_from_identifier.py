from typing import Type

from pydantic import BaseModel

from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetSecurityIdFromIdentifier(KfinanceTool):
    name: str = "get_security_id_from_identifier"
    description: str = "Get the security id associated with an identifier."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier

    def _run(self, identifier: str) -> int:
        return self.kfinance_client.ticker(identifier).security_id
