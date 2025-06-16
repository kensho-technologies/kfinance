from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool


class GetCompanyAlternateNamesFromIdentifier(KfinanceTool):
    name: str = "get_company_alternate_names_from_identifier"
    description: str = "Gets all known alternate names a company might go by (for example, Hewlett-Packard Company also goes by the name HP)."
    required_permission: Permission | None = Permission.IntelligencePermission

    def _run(
        self,
        identifier: str,
    ) -> dict:
        ticker = self.kfinance_client.ticker(identifier)
        return self.kfinance_client.kfinance_api_client.fetch_company_other_names(
            company_id=ticker.company_id
        )["alternate_names"]