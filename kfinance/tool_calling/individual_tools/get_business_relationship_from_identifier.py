from textwrap import dedent
from typing import Type

from pydantic import BaseModel

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.constants import BusinessRelationshipType, Permission, ToolMode, COMPANY_ID_PREFIX
from kfinance.kfinance import BusinessRelationships
from kfinance.tool_calling.group_tools.company_identifiers import parse_identifiers
from kfinance.tool_calling.group_tools.identifier_resolvers import \
    fetch_company_ids_from_identifiers
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifiers


class GetBusinessRelationshipFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    business_relationship: BusinessRelationshipType


class GetBusinessRelationshipFromIdentifiers(KfinanceTool):
    name: str = "get_business_relationship_from_identifiers"
    description: str = dedent("""
        Get the current and previous company IDs that are relationship_type for a list of identifiers. 
        
        Example: 
        Query: "What are the previous borrowers of SPGI and JPM?"
        Function: get_business_relationship_from_identifiers(identifiers=["SPGI", "JPM"], business_relationship=BusinessRelationshipType.borrower)
    """).strip()
    args_schema: Type[BaseModel] = GetBusinessRelationshipFromIdentifiersArgs
    required_permission: Permission | None = Permission.RelationshipPermission
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(self, identifiers: list[str], business_relationship: BusinessRelationshipType) -> dict:

        parsed_identifiers = parse_identifiers(identifiers)
        identifiers_to_company_ids = fetch_company_ids_from_identifiers(
            identifiers=parsed_identifiers, api_client=self.kfinance_client.kfinance_api_client
        )

        tasks = [
            Task(
                func=self.kfinance_client.kfinance_api_client.fetch_companies_from_business_relationship,
                kwargs=dict(
                    company_id=company_id,
                    relationship_type=business_relationship,
                ),
                result_key=identifier,
            )
            for identifier, company_id in identifiers_to_company_ids.items()
        ]

        relationship_responses = process_tasks_in_thread_pool_executor(
            api_client=self.kfinance_client.kfinance_api_client, tasks=tasks
        )

        for identifier, result in relationship_responses.items():
            for group in ["current", "previous"]:
                for company in result[group]:
                    company["company_id"] = f"{COMPANY_ID_PREFIX}{company['company_id']}"
        return {str(id): result for id, result in relationship_responses.items()}
