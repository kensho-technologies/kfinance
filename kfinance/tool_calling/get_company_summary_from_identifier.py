from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier

class GetCompanySummaryFromIdentifier(KfinanceTool):
    name: str = "get_company_summary_from_identifier"
    description: str = "Gets a one paragraph summary/short description of a company, including information about the company's primary business, products and services offered and their applications, business segment details, client/customer groups served, geographic markets served, distribution channels, strategic alliances/partnerships, founded/incorporated year, latest former name, and headquarters and additional offices."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = Permission.IntelligencePermission

    def _run(
        self,
        identifier: str,
    ) -> dict:
        ticker = self.kfinance_client.ticker(identifier)
        return ticker.summary
