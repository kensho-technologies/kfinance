from textwrap import dedent
from typing import Type

from pydantic import BaseModel

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.permission_models import Permission
from kfinance.domains.business_relationships.business_relationship_models import (
    BusinessRelationshipType,
    RelationshipResponse,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
)


class GetBusinessRelationshipFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    business_relationship: BusinessRelationshipType


class GetBusinessRelationshipFromIdentifiersResp(BaseModel):
    business_relationship: BusinessRelationshipType
    results: dict[str, RelationshipResponse]
    errors: list[str]


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

    def _run(
        self, identifiers: list[str], business_relationship: BusinessRelationshipType
    ) -> GetBusinessRelationshipFromIdentifiersResp:
        """Sample response:

        {
            'business_relationship': 'supplier',
            'results': {
                'SPGI': {
                    'current': [
                        {'company_id': 'C_883103', 'company_name': 'CRISIL Limited'}
                    ],
                    'previous': [
                        {'company_id': 'C_472898', 'company_name': 'Morgan Stanley'},
                        {'company_id': 'C_8182358', 'company_name': 'Eloqua, Inc.'}
                    ]
                }
            },
            'errors': ['No identification triple found for the provided identifier: NON-EXISTENT of type: ticker']}
        """

        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)

        tasks = [
            Task(
                func=api_client.fetch_companies_from_business_relationship,
                kwargs=dict(
                    company_id=id_triple.company_id,
                    relationship_type=business_relationship,
                ),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]

        relationship_responses = process_tasks_in_thread_pool_executor(
            api_client=api_client, tasks=tasks
        )

        return GetBusinessRelationshipFromIdentifiersResp(
            business_relationship=business_relationship,
            results=relationship_responses,
            errors=list(id_triple_resp.errors.values()),
        )
