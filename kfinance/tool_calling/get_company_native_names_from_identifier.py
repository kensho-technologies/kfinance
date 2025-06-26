from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetCompanyNativeNamesFromIdentifier(KfinanceTool):
    name: str = "get_company_native_names_from_identifier"
    description: str = "Gets the primary non-Latin character native names for global companies, including languages such as Arabic, Russian, Greek, Japanese, etc. This also includes limited history on native name changes."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = Permission.IntelligencePermission

    def _run(
        self,
        identifier: str,
    ) -> list[dict[str, str]]:
        ticker = self.kfinance_client.ticker(identifier)
        return [native_name.model_dump(mode="json") for native_name in ticker.native_names]