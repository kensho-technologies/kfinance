from typing import Type

from pydantic import BaseModel

from kfinance.constants import BusinessRelationshipType, Permission, ToolMode
from kfinance.kfinance import BusinessRelationships
from kfinance.tool_calling.shared_models import KfinanceTool


class GetBusinessRelationshipFromCompanyIdArgs(BaseModel):
    company_id: int
    # no description because the description for enum fields comes from the enum docstring.
    business_relationship: BusinessRelationshipType


class GetBusinessRelationshipFromCompanyId(KfinanceTool):
    name: str = "get_business_relationship_from_company_id"
    description: str = 'Get the current and previous company IDs that are relationship_type of a given company_id. For example, "What are the current distributors of SPGI?" or "What are the previous borrowers of JPM?"'
    args_schema: Type[BaseModel] = GetBusinessRelationshipFromCompanyIdArgs
    required_permission: Permission | None = Permission.RelationshipPermission
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(self, company_id: int, business_relationship: BusinessRelationshipType) -> dict:
        company = self.kfinance_client.company(company_id)
        business_relationship_obj: BusinessRelationships = getattr(
            company, business_relationship.value
        )
        return {
            "current": [
                dict(company_id=company.company_id) for company in business_relationship_obj.current
            ],
            "previous": [
                dict(company_id=company.company_id)
                for company in business_relationship_obj.previous
            ],
        }
