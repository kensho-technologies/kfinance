from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetInfoFromIdentifier(KfinanceTool):
    name: str = "get_info_from_identifier"
    description: str = "Get the information associated with an identifier. Info includes company name, status, type, simple industry, number of employees (if available), founding date, webpage, HQ address, HQ city, HQ zip code, HQ state, HQ country, and HQ country iso code."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = None

    def _run(self, identifier: str) -> str:
        return str(self.kfinance_client.ticker(identifier).info)
