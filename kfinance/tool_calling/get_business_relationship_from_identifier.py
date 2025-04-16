from typing import Type

from pydantic import BaseModel, Field

from kfinance.constants import BusinessRelationshipType
from kfinance.kfinance import BusinessRelationships
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetBusinessRelationshipFromIdentifierArgs(ToolArgsWithIdentifier):
    business_relationship: BusinessRelationshipType = Field(
        description="The type of business relationship requested"
    )


class GetBusinessRelationshipFromIdentifier(KfinanceTool):
    name: str = "get_business_relationship_from_identifier"
    description: str = 'Get the current and previous company IDs that are relationship_type of a given identifier. For example, "What are the current distributors of SPGI?" or "What are the previous borrowers of JPM?"'
    args_schema: Type[BaseModel] = GetBusinessRelationshipFromIdentifierArgs

    def _run(self, identifier: str, business_relationship: BusinessRelationshipType) -> dict:
        ticker = self.kfinance_client.ticker(identifier)
        business_relationship_obj: BusinessRelationships = getattr(
            ticker, business_relationship.value
        )
        return {
            "current": [company.company_id for company in business_relationship_obj.current],
            "previous": [company.company_id for company in business_relationship_obj.previous],
        }
