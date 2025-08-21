from typing import Type

from pydantic import BaseModel

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.permission_models import Permission
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
)


class GetCusipOrIsinFromIdentifiersResp(ToolRespWithErrors):
    """Both cusip and isin return a mapping from identifier to str (isin or cusip)."""

    results: dict[str, str]


class GetCusipFromIdentifiers(KfinanceTool):
    name: str = "get_cusip_from_identifiers"
    description: str = "Get the CUSIPs for a group of identifiers."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.IDPermission}

    def _run(self, identifiers: list[str]) -> GetCusipOrIsinFromIdentifiersResp:
        """Sample response:

        {
            'results': {'SPGI': '78409V104'},
            'errors': ['Kensho is a private company without a security_id.']
        }
        """
        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)
        id_triple_resp.filter_out_companies_without_security_ids()

        tasks = [
            Task(
                func=api_client.fetch_cusip,
                kwargs=dict(security_id=id_triple.security_id),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]

        cusip_responses = process_tasks_in_thread_pool_executor(api_client=api_client, tasks=tasks)
        return GetCusipOrIsinFromIdentifiersResp(
            results={
                identifier: cusip_resp["cusip"]
                for identifier, cusip_resp in cusip_responses.items()
            },
            errors=list(id_triple_resp.errors.values()),
        )


class GetIsinFromIdentifiers(KfinanceTool):
    name: str = "get_isin_from_identifiers"
    description: str = "Get the ISINs for a group of identifiers."
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.IDPermission}

    def _run(self, identifiers: list[str]) -> GetCusipOrIsinFromIdentifiersResp:
        """Sample response:

        {
            'results': {'SPGI': 'US78409V104'},
            'errors': ['Kensho is a private company without a security_id.']
        }
        """
        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)
        id_triple_resp.filter_out_companies_without_security_ids()

        tasks = [
            Task(
                func=api_client.fetch_isin,
                kwargs=dict(security_id=id_triple.security_id),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]

        isin_responses = process_tasks_in_thread_pool_executor(api_client=api_client, tasks=tasks)
        return GetCusipOrIsinFromIdentifiersResp(
            results={
                identifier: isin_resp["isin"] for identifier, isin_resp in isin_responses.items()
            },
            errors=list(id_triple_resp.errors.values()),
        )
