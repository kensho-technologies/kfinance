from textwrap import dedent
from typing import Type

import httpx
from pydantic import BaseModel

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.business_relationships.business_relationship_models import (
    BusinessRelationshipType,
    RelationshipResponse,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithIdInfoAndErrors,
)


class GetBusinessRelationshipFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    business_relationship: BusinessRelationshipType


class GetBusinessRelationshipFromIdentifiersResp(ToolRespWithIdInfoAndErrors[RelationshipResponse]):
    business_relationship: BusinessRelationshipType


class GetBusinessRelationshipFromIdentifiers(KfinanceTool):
    name: str = "get_business_relationship_from_identifiers"
    description: str = dedent("""
        Get the current and previous companies that have a specified business relationship with each of the provided identifiers.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - Results include both "current" (active) and "previous" (historical) relationships.

        Examples:
        Query: "Who are the current and previous suppliers of Intel?"
        Function: get_business_relationship_from_identifiers(identifiers=["Intel"], business_relationship="supplier")

        Query: "What are the borrowers of SPGI and JPM?"
        Function: get_business_relationship_from_identifiers(identifiers=["SPGI", "JPM"], business_relationship="borrower")

        Query: "Who are Dell's customers?"
        Function: get_business_relationship_from_identifiers(identifiers=["Dell"], business_relationship="customer")
    """).strip()
    args_schema: Type[BaseModel] = GetBusinessRelationshipFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.RelationshipPermission}

    async def _arun(
        self, identifiers: list[str], business_relationship: BusinessRelationshipType
    ) -> GetBusinessRelationshipFromIdentifiersResp:
        """"""
        return await get_business_relationship_from_identifiers(
            identifiers=identifiers,
            business_relationship=business_relationship,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def get_business_relationship_from_identifiers(
    identifiers: list[str],
    business_relationship: BusinessRelationshipType,
    httpx_client: httpx.AsyncClient,
) -> GetBusinessRelationshipFromIdentifiersResp:
    """Fetch business relationships for all identifiers.

    Sample Response:
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

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_business_relationship_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                business_relationship=business_relationship,
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

    return GetBusinessRelationshipFromIdentifiersResp(
        business_relationship=business_relationship,
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
    )


async def fetch_business_relationship_from_company_id(
    company_id: int,
    business_relationship: BusinessRelationshipType,
    httpx_client: httpx.AsyncClient,
) -> RelationshipResponse:
    """Fetch and return business relationship for one identifier."""
    resp = await httpx_client.get(url=f"/relationship/{company_id}/{business_relationship}")
    resp.raise_for_status()
    return RelationshipResponse.model_validate(resp.json())
