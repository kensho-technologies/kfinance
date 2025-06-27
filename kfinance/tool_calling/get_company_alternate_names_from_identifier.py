from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetCompanyAlternateNamesFromIdentifier(KfinanceTool):
    name: str = "get_company_alternate_names_from_identifier"
    description: str = "Gets all known alternate names a company might go by (for example, Hewlett-Packard Company also goes by the name HP)."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = Permission.IntelligencePermission

    def _run(
        self,
        identifier: str,
    ) -> list[str]:
        ticker = self.kfinance_client.ticker(identifier)
        return ticker.alternate_names
