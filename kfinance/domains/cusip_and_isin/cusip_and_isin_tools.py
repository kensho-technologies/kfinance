from textwrap import dedent
from typing import Literal, Type

import httpx
from pydantic import BaseModel

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithIdInfoAndErrors,
)


class GetCusipOrIsinFromIdentifiersResp(ToolRespWithIdInfoAndErrors[str]):
    """Both cusip and isin return a mapping from identifier to str (isin or cusip)."""

    pass


class GetCusipFromIdentifiers(KfinanceTool):
    name: str = "get_cusip_from_identifiers"
    description: str = dedent("""
        Get the CUSIPs for a group of identifiers.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.

        Examples:
        Query: "What is the CUSIP for Humana?"
        Function: get_cusip_from_identifiers(identifiers=["Humana"])

        Query: "Get CUSIPs for ATO and DTE"
        Function: get_cusip_from_identifiers(identifiers=["ATO", "DTE"])
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.IDPermission}

    async def _arun(self, identifiers: list[str]) -> GetCusipOrIsinFromIdentifiersResp:
        """"""
        return await get_cusip_or_isin_from_identifiers(
            identifiers=identifiers,
            cusip_or_isin="cusip",
            httpx_client=self.kfinance_client.httpx_client,
        )


class GetIsinFromIdentifiers(KfinanceTool):
    name: str = "get_isin_from_identifiers"
    description: str = dedent("""
        Get the ISINs for a group of identifiers.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.

        Examples:
        Query: "What is the ISIN for Autodesk?"
        Function: get_isin_from_identifiers(identifiers=["Autodesk"])

        Query: "Get ISINs for RCL and CCL"
        Function: get_isin_from_identifiers(identifiers=["RCL", "CCL"])
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.IDPermission}

    async def _arun(self, identifiers: list[str]) -> GetCusipOrIsinFromIdentifiersResp:
        """"""
        return await get_cusip_or_isin_from_identifiers(
            identifiers=identifiers,
            cusip_or_isin="isin",
            httpx_client=self.kfinance_client.httpx_client,
        )


async def get_cusip_or_isin_from_identifiers(
    identifiers: list[str],
    cusip_or_isin: Literal["cusip", "isin"],
    httpx_client: httpx.AsyncClient,
) -> GetCusipOrIsinFromIdentifiersResp:
    """Fetch cusips or isins for identifiers

    Sample response:

        {
            'results': {
                'SPGI': {
                    'company_name': 'SP Global Inc.',
                    'ticker': 'NYSE:SPGI',
                    'country': 'USA',
                    'data': '78409V104'
                }
            },
            'errors': ['Kensho is a private company without a security_id.']
        }
    """

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    id_triple_resp.filter_out_companies_without_security_ids()
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_cusip_or_isin_from_security_id,
            kwargs=dict(
                security_id=id_triple.security_id,
                cusip_or_isin=cusip_or_isin,
                httpx_client=httpx_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, str] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            results[task.result_key] = task.result

    return GetCusipOrIsinFromIdentifiersResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
    )


async def fetch_cusip_or_isin_from_security_id(
    security_id: int,
    cusip_or_isin: Literal["cusip", "isin"],
    httpx_client: httpx.AsyncClient,
) -> str:
    """Fetch and return the cusip or isin for a security id."""
    url = f"/{cusip_or_isin}/{security_id}"
    resp = await httpx_client.get(url=url)
    resp.raise_for_status()
    return resp.json()[cusip_or_isin]
