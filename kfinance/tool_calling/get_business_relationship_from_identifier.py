from typing import Type

from pydantic import BaseModel

from kfinance.constants import BusinessRelationshipType, Permission
from kfinance.kfinance import BusinessRelationships
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetBusinessRelationshipFromIdentifierArgs(ToolArgsWithIdentifier):
    # no description because the description for enum fields comes from the enum docstring.
    business_relationship: BusinessRelationshipType


class GetBusinessRelationshipFromIdentifier(KfinanceTool):
    name: str = "get_business_relationship_from_identifier"
    description: str = 'Get the current and previous company IDs that are relationship_type of a given identifier. For example, "What are the current distributors of SPGI?" or "What are the previous borrowers of JPM?"'
    args_schema: Type[BaseModel] = GetBusinessRelationshipFromIdentifierArgs
    required_permission: Permission | None = Permission.RelationshipPermission

    def _run(self, identifier: str, business_relationship: BusinessRelationshipType) -> dict:
        ticker = self.kfinance_client.ticker(identifier)
        business_relationship_obj: BusinessRelationships = getattr(
            ticker, business_relationship.value
        )
        return {
            "current": [company.company_id for company in business_relationship_obj.current],
            "previous": [company.company_id for company in business_relationship_obj.previous],
        }
