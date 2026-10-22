from textwrap import dedent
from typing import Type

import httpx2
from pydantic import BaseModel

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.relationships.relationship_models import (
    AnyRelationshipType,
    BusinessRelationshipType,
    CompanyRelationshipType,
    RelationshipResponse,
    RelationshipType,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithIdInfoAndErrors,
)


class GetRelationshipFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    relationship_type: RelationshipType


# Args models for clients entitled to only one of the two datasets. Swapped in by
# `GetRelationshipFromIdentifiers.apply_user_permissions` so that the LLM is never offered a
# relationship type the server would reject due to entitlements.
class GetBusinessRelationshipFromIdentifiersArgs(ToolArgsWithIdentifiers):
    relationship_type: BusinessRelationshipType


class GetCompanyRelationshipFromIdentifiersArgs(ToolArgsWithIdentifiers):
    relationship_type: CompanyRelationshipType


class GetRelationshipFromIdentifiersResp(ToolRespWithIdInfoAndErrors[RelationshipResponse]):
    relationship_type: RelationshipType


_BASE_DESCRIPTION = dedent("""
    Get the companies that have a specified relationship with each of the provided identifiers.

    - When possible, pass multiple identifiers in a single call rather than making multiple calls.
    - Results include both "current" (active) and "previous" (historical) relationships.
    - Some relationship types may additionally include "cancelled" and "pending" relationships.

    Examples:
""").strip()

_BUSINESS_RELATIONSHIP_EXAMPLES = dedent("""
    Query: "Who are the current and previous suppliers of Intel?"
    Function: get_relationship_from_identifiers(identifiers=["Intel"], relationship_type="supplier")

    Query: "What are the borrowers of SPGI and JPM?"
    Function: get_relationship_from_identifiers(identifiers=["SPGI", "JPM"], relationship_type="borrower")

    Query: "Who are Dell's customers?"
    Function: get_relationship_from_identifiers(identifiers=["Dell"], relationship_type="customer")
""").strip()

_COMPANY_RELATIONSHIP_EXAMPLES = dedent("""
    Query: "Which funds does BlackRock sponsor?"
    Function: get_relationship_from_identifiers(identifiers=["BlackRock"], relationship_type="sponsored_fund")
""").strip()

_FULL_DESCRIPTION = (
    f"{_BASE_DESCRIPTION}\n\n{_BUSINESS_RELATIONSHIP_EXAMPLES}\n\n{_COMPANY_RELATIONSHIP_EXAMPLES}"
)


class GetRelationshipFromIdentifiers(KfinanceTool):
    name: str = "get_relationship_from_identifiers"
    description: str = _FULL_DESCRIPTION
    args_schema: Type[BaseModel] = GetRelationshipFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {
        Permission.BusinessRelationshipsPermission,
        Permission.CompanyRelationshipsPermission,
    }

    def apply_user_permissions(self, permissions: set[Permission]) -> None:
        """Restrict the relationship types to the datasets this client is entitled to query."""
        has_business = Permission.BusinessRelationshipsPermission in permissions
        has_company = Permission.CompanyRelationshipsPermission in permissions
        if has_business and not has_company:
            self.args_schema = GetBusinessRelationshipFromIdentifiersArgs
            self.description = f"{_BASE_DESCRIPTION}\n\n{_BUSINESS_RELATIONSHIP_EXAMPLES}"
        elif has_company and not has_business:
            self.args_schema = GetCompanyRelationshipFromIdentifiersArgs
            self.description = f"{_BASE_DESCRIPTION}\n\n{_COMPANY_RELATIONSHIP_EXAMPLES}"

    async def _arun(
        self, identifiers: list[str], relationship_type: AnyRelationshipType
    ) -> GetRelationshipFromIdentifiersResp:
        """"""
        return await get_relationship_from_identifiers(
            identifiers=identifiers,
            relationship_type=relationship_type,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def get_relationship_from_identifiers(
    identifiers: list[str],
    relationship_type: AnyRelationshipType,
    httpx_client: httpx2.AsyncClient,
) -> GetRelationshipFromIdentifiersResp:
    """Fetch relationships for all identifiers.

    "pending" and "cancelled" statuses are only returned only for some relationship types, and only
    for clients entitled to them.

    Sample Response:
    {
        'relationship_type': 'supplier',
        'results': {
            'SPGI': {
                'company_name': 'S&P Global Inc.',
                'ticker': 'NYSE:SPGI',
                'country': 'USA',
                'data': {
                    'current': [
                        {'company_id': 'C_883103', 'company_name': 'CRISIL Limited'}
                    ],
                    'previous': [
                        {'company_id': 'C_472898', 'company_name': 'Morgan Stanley'},
                        {'company_id': 'C_8182358', 'company_name': 'Eloqua, Inc.'}
                    ]
                }
            }
        },
        'errors': ['No identification triple found for the provided identifier: NON-EXISTENT of type: ticker']}
    """

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_relationship_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                relationship_type=relationship_type,
                httpx_client=httpx_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, RelationshipResponse] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            results[task.result_key] = task.result

    return GetRelationshipFromIdentifiersResp(
        relationship_type=relationship_type,
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
    )


async def fetch_relationship_from_company_id(
    company_id: int,
    relationship_type: AnyRelationshipType,
    httpx_client: httpx2.AsyncClient,
) -> RelationshipResponse:
    """Fetch and return a relationship for one identifier."""
    resp = await httpx_client.get(url=f"/relationship/{company_id}/{relationship_type}")
    resp.raise_for_status()
    return RelationshipResponse.model_validate(resp.json())
