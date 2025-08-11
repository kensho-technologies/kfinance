from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetCompanyDescriptionFromIdentifier(KfinanceTool):
    name: str = "get_company_description_from_identifier"
    description: str = "Gets a detailed description of a company, broken down into sections, which may include information about the company's Primary business, Segments (including Products and Services for each), Competition, Significant events, and History. Within the text, four spaces represent a new paragraph. Note that the description is divided into sections with headers, where each section has a new paragraph (four spaces) before and after the section header."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = Permission.CompanyIntelligencePermission

    def _run(
        self,
        identifier: str,
    ) -> str:
        ticker = self.kfinance_client.ticker(identifier)
        return ticker.description
