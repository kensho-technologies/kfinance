from functools import lru_cache
from textwrap import dedent
from typing import Type

import httpx
from pydantic import BaseModel, create_model
from strenum import StrEnum

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.relationships.relationship_models import (
    RelationshipResponse,
    RelationshipType,
    permitted_relationship_types,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithIdInfoAndErrors,
)


class GetRelationshipFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    relationship_type: RelationshipType


@lru_cache(maxsize=8)
def build_relationship_args_model(
    permitted: frozenset[RelationshipType],
) -> Type[BaseModel]:
    """Build an args model whose relationship_type enum is restricted to `permitted`.

    Used to hide relationship types a client isn't entitled to from the LLM. The derived
    enum members are distinct objects from their RelationshipType counterparts but carry
    the same values, so they interpolate into request urls identically.
    """
    members = {
        relationship_type.name: relationship_type.value
        for relationship_type in RelationshipType
        if relationship_type in permitted
    }
    # StrEnum's functional api accepts a name-to-value mapping, which its stub doesn't cover.
    restricted_enum = StrEnum("RelationshipType", members)  # type: ignore[arg-type]
    # pydantic emits the enum docstring as the field description.
    restricted_enum.__doc__ = RelationshipType.__doc__
    return create_model(
        "GetRelationshipFromIdentifiersArgs",
        __base__=ToolArgsWithIdentifiers,
        relationship_type=(restricted_enum, ...),
    )


class GetRelationshipFromIdentifiersResp(ToolRespWithIdInfoAndErrors[RelationshipResponse]):
    relationship_type: RelationshipType


_BASE_DESCRIPTION = dedent("""
    Get the current and previous companies that have a specified relationship with each of the provided identifiers.

    - When possible, pass multiple identifiers in a single call rather than making multiple calls.
    - Results include both "current" (active) and "previous" (historical) relationships.

    Examples:
    Query: "Who are the current and previous suppliers of Intel?"
    Function: get_relationship_from_identifiers(identifiers=["Intel"], relationship_type="supplier")

    Query: "What are the borrowers of SPGI and JPM?"
    Function: get_relationship_from_identifiers(identifiers=["SPGI", "JPM"], relationship_type="borrower")

    Query: "Who are Dell's customers?"
    Function: get_relationship_from_identifiers(identifiers=["Dell"], relationship_type="customer")
""").strip()

# Appended to the description only for clients entitled to the fund relationship types.
_CR_ONLY_DESCRIPTION = dedent("""
    The fund relationship types (fund_sponsor, sponsored_fund, fund_family, fund_family_member,
    fund_distributor, distributed_fund, fund_investment_advisor, advised_fund) additionally return
    "pending" (announced but not yet effective) and "cancelled" (announced but abandoned)
    relationships.

    Query: "Which funds does BlackRock sponsor?"
    Function: get_relationship_from_identifiers(identifiers=["BlackRock"], relationship_type="sponsored_fund")
""").strip()


class GetRelationshipFromIdentifiers(KfinanceTool):
    name: str = "get_relationship_from_identifiers"
    description: str = f"{_BASE_DESCRIPTION}\n\n{_CR_ONLY_DESCRIPTION}"
    args_schema: Type[BaseModel] = GetRelationshipFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.RelationshipPermission}

    def apply_user_permissions(self, permissions: set[Permission]) -> None:
        """Hide the relationship types this client isn't entitled to query."""
        permitted = permitted_relationship_types(permissions)
        if permitted != frozenset(RelationshipType):
            self.description = _BASE_DESCRIPTION
            self.args_schema = build_relationship_args_model(permitted)

    async def _arun(
        self, identifiers: list[str], relationship_type: RelationshipType
    ) -> GetRelationshipFromIdentifiersResp:
        """"""
        return await get_relationship_from_identifiers(
            identifiers=identifiers,
            relationship_type=relationship_type,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def get_relationship_from_identifiers(
    identifiers: list[str],
    relationship_type: RelationshipType,
    httpx_client: httpx.AsyncClient,
) -> GetRelationshipFromIdentifiersResp:
    """Fetch relationships for all identifiers.

    "pending" and "cancelled" are only returned for the fund relationship types, and only
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
    relationship_type: RelationshipType,
    httpx_client: httpx.AsyncClient,
) -> RelationshipResponse:
    """Fetch and return a relationship for one identifier."""
    resp = await httpx_client.get(url=f"/relationship/{company_id}/{relationship_type}")
    resp.raise_for_status()
    return RelationshipResponse.model_validate(resp.json())
