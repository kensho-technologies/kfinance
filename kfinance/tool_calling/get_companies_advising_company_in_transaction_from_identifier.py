from typing import Type

from pydantic import BaseModel, Field

from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetCompaniesAdvisingCompanyInTransactionFromIdentifierArgs(ToolArgsWithIdentifier):
    transaction_id: int | None = Field(description="The ID of the merger.", default=None)


class GetCompaniesAdvisingCompanyInTransactionFromIdentifier(KfinanceTool):
    name: str = "get_companies_advising_company_in_transaction_from_identifier"
    description: str = 'Get the companies advising a company in a given transaction. For example, "Who advised S&P Global during their purchase of Kenhso?"'
    args_schema: Type[BaseModel] = GetCompaniesAdvisingCompanyInTransactionFromIdentifierArgs
    required_permission: Permission | None = Permission.MergersPermission

    def _run(self, identifier: str, transaction_id: int) -> list:
        ticker = self.kfinance_client.ticker(identifier)
        ticker.company.transaction_id = transaction_id
        advisors = ticker.company.advisors

        if advisors:
            return [
                {
                    "advisor_company_id": advisor.company_id,
                    "advisor_type_name": advisor.advisor_type_name,
                }
                for advisor in advisors
            ]
        else:
            return []
