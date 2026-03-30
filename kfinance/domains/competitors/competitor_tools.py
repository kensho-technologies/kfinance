from textwrap import dedent
from typing import Type

import httpx

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.competitors.competitor_models import CompetitorResponse, CompetitorSource
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
)


class GetCompetitorsFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    competitor_source: CompetitorSource


class GetCompetitorsFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, CompetitorResponse]


class GetCompetitorsFromIdentifiers(KfinanceTool):
    name: str = "get_competitors_from_identifiers"
    description: str = dedent("""
        Retrieves a list of company_id and company_name that are competitors for a list of companies, filtered by the source of the competitor information.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - Available competitor sources: all, filing (from SEC filings), key_dev (from key developments), contact (from contact relationships), third_party (from third-party sources), self_identified (self-identified), named_by_competitor (from competitor's perspective)

        Examples:
        Query: "Who are Microsoft's competitors from SEC filings?"
        Function: get_competitors_from_identifiers(identifiers=["Microsoft"], competitor_source="filing")

        Query: "Get all competitors of AAPL and GOOGL"
        Function: get_competitors_from_identifiers(identifiers=["AAPL", "GOOGL"], competitor_source="all")
    """).strip()
    args_schema: Type[GetCompetitorsFromIdentifiersArgs] = GetCompetitorsFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.CompetitorsPermission}

    async def _arun(
        self,
        identifiers: list[str],
        competitor_source: CompetitorSource,
    ) -> GetCompetitorsFromIdentifiersResp:
        """"""
        return await get_competitors_from_identifiers(
            identifiers=identifiers,
            competitor_source=competitor_source,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def get_competitors_from_identifiers(
    identifiers: list[str],
    competitor_source: CompetitorSource,
    httpx_client: httpx.AsyncClient,
) -> GetCompetitorsFromIdentifiersResp:
    """Fetch competitors for all identifiers.

    Sample response:

    {
        "results": {
            "SPGI": {
                {'company_id': "C_35352", 'company_name': 'The Descartes Systems Group Inc.'},
                {'company_id': "C_4003514", 'company_name': 'London Stock Exchange Group plc'}
            }
        },
        'errors': ['No identification triple found for the provided identifier: NON-EXISTENT of type: ticker']
    }
    """

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_competitors_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                competitor_source=competitor_source,
                httpx_client=httpx_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, CompetitorResponse] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            results[task.result_key] = task.result

    resp_model = GetCompetitorsFromIdentifiersResp(results=results, errors=errors)
    return resp_model


async def fetch_competitors_from_company_id(
    company_id: int,
    competitor_source: CompetitorSource,
    httpx_client: httpx.AsyncClient,
) -> CompetitorResponse:
    """Fetch and return competitors for one identifier."""
    url = f"/competitors/{company_id}"
    if competitor_source is not CompetitorSource.all:
        url = url + f"/{competitor_source}"
    resp = await httpx_client.get(url=url)
    resp.raise_for_status()
    return CompetitorResponse.model_validate(resp.json())
