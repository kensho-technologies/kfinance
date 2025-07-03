from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetCompanySummaryAndDescriptionFromIdentifier(KfinanceTool):
    name: str = "get_company_summary_and_description_from_identifier"
    description: str = "Gets a company's summary and description. The summary is a one paragraph, short description of a company, including information about the company's primary business, products and services offered and their applications, business segment details, client/customer groups served, geographic markets served, distribution channels, strategic alliances/partnerships, founded/incorporated year, latest former name, and headquarters and additional offices. The company's description is a longer, detailed description of a company, broken down into sections, which may include information about the company's Primary business, Segments (including Products and Services for each), Competition, Significant events, and History. Within the text, four spaces represent a new paragraph. Note that the description is divided into sections with headers, where each section has a new paragraph (four spaces) before and after the section header."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = Permission.IntelligencePermission

    def _run(
        self,
        identifier: str,
    ) -> dict[str, str]:
        ticker = self.kfinance_client.ticker(identifier)
        return {
            "summary": ticker.summary,
            "description": ticker.description,
        }
