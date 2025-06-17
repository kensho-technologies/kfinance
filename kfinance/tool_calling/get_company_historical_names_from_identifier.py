from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetCompanyHistoricalNamesFromIdentifier(KfinanceTool):
    name: str = "get_company_historical_names_from_identifier"
    description: str = "Gets all known historical names if the company's name has changed over time."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = Permission.IntelligencePermission

    def _run(
        self,
        identifier: str,
    ) -> dict:
        ticker = self.kfinance_client.ticker(identifier)
        return ticker.company.historical_names()
