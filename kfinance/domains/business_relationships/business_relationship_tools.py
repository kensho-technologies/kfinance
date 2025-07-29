from textwrap import dedent
from typing import Type

from pydantic import BaseModel

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.permission_models import Permission
from kfinance.domains.business_relationships.business_relationship_models import (
    BusinessRelationshipType,
)
from kfinance.domains.companies.company_identifiers import (
    fetch_company_ids_from_identifiers,
    parse_identifiers,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
)


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
    accepted_permissions: set[Permission] | None = {Permission.RelationshipPermission}

    def _run(self, identifiers: list[str], business_relationship: BusinessRelationshipType) -> dict:
        """Sample response:

        {
            "SPGI": {
                "current": [{"company_id": "C_883103", "company_name": "CRISIL Limited"}],
                "previous": [
                    {"company_id": "C_472898", "company_name": "Morgan Stanley"},
                    {"company_id": "C_8182358", "company_name": "Eloqua, Inc."},
                ],
            }
        }
        """

        api_client = self.kfinance_client.kfinance_api_client
        parsed_identifiers = parse_identifiers(identifiers=identifiers, api_client=api_client)
        identifiers_to_company_ids = fetch_company_ids_from_identifiers(
            identifiers=parsed_identifiers, api_client=api_client
        )

        tasks = [
            Task(
                func=api_client.fetch_companies_from_business_relationship,
                kwargs=dict(
                    company_id=company_id,
                    relationship_type=business_relationship,
                ),
                result_key=identifier,
            )
            for identifier, company_id in identifiers_to_company_ids.items()
        ]

        relationship_responses = process_tasks_in_thread_pool_executor(
            api_client=api_client, tasks=tasks
        )

        return {str(k): v.model_dump(mode="json") for k, v in relationship_responses.items()}
