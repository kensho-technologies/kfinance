from typing import Type

from pydantic import BaseModel

from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetCompanyIdFromIdentifier(KfinanceTool):
    name: str = "get_company_id_from_identifier"
    description: str = "Get the company id associated with an identifier."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier

    def _run(self, identifier: str) -> int:
        return self.kfinance_client.ticker(identifier).company_id
