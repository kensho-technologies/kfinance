from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool


class GetCompanySummaryFromIdentifier(KfinanceTool):
    name: str = "get_company_summary_from_identifier"
    description: str = "Retrieves a list of competitors for a given company, optionally filtered by the source of the competitor information."
    required_permission: Permission | None = Permission.IntelligencePermission

    def _run(
        self,
        identifier: str,
    ) -> dict:
        ticker = self.kfinance_client.ticker(identifier)
        return self.kfinance_client.kfinance_api_client.fetch_company_summary(
            company_id=ticker.company_id
        )