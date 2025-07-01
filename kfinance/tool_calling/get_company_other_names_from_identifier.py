from typing import Any, Type

from pydantic import BaseModel

from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetCompanyOtherNamesFromIdentifier(KfinanceTool):
    name: str = "get_company_other_names_from_identifier"
    description: str = "Gets a company's alternate, historical, and native names. Alternate names are additional names a company might go by (for example, Hewlett-Packard Company also goes by the name HP). Historical names are previous names for the company if it has changed over time. Native names are primary non-Latin character native names for global companies, including languages such as Arabic, Russian, Greek, Japanese, etc. This also includes limited history on native name changes."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = Permission.IntelligencePermission

    def _run(
        self,
        identifier: str,
    ) -> dict[str, Any]:
        ticker = self.kfinance_client.ticker(identifier)
        return {
            "alternate_names": ticker.alternate_names,
            "historical_names": ticker.historical_names,
            "native_names": ticker.native_names,
        }
