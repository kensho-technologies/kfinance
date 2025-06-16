from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool


class GetCompanyHistoricalNamesFromIdentifier(KfinanceTool):
    name: str = "get_company_historical_names_from_identifier"
    description: str = "Gets all known historical names if the company's name has changed over time."
    required_permission: Permission | None = Permission.IntelligencePermission

    def _run(
        self,
        identifier: str,
    ) -> dict:
        ticker = self.kfinance_client.ticker(identifier)
        return self.kfinance_client.kfinance_api_client.fetch_company_other_names(
            company_id=ticker.company_id
        )["historical_names"]