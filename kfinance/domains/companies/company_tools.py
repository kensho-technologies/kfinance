from textwrap import dedent
from typing import Type

from pydantic import BaseModel

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.permission_models import Permission
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
)


class GetInfoFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, dict]


class GetInfoFromIdentifiers(KfinanceTool):
    name: str = "get_info_from_identifiers"
    description: str = dedent("""
        Get the information associated with a list of identifiers. Info includes company name, status, type, simple industry, number of employees (if available), founding date, webpage, HQ address, HQ city, HQ zip code, HQ state, HQ country, and HQ country iso code.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = None

    def _run(self, identifiers: list[str]) -> dict:
        """Sample response:

        {   "results": {
                "SPGI": {
                    "name": "S&P Global Inc.",
                    "status": "Operating",
                    "type": "Public Company",
                    "simple_industry": "Capital Markets",
                    "number_of_employees": "42350.0000",
                    "founding_date": "1860-01-01",
                    "webpage": "www.spglobal.com",
                    "address": "55 Water Street",
                    "city": "New York",
                    "zip_code": "10041-0001",
                    "state": "New York",
                    "country": "United States",
                    "iso_country": "USA"
                }
            },
            "errors": [['No identification triple found for the provided identifier: NON-EXISTENT of type: ticker']
        }
        """
        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)

        tasks = [
            Task(
                func=api_client.fetch_info,
                kwargs=dict(company_id=id_triple.company_id),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]

        info_responses: dict[str, dict] = process_tasks_in_thread_pool_executor(
            api_client=api_client, tasks=tasks
        )
        resp_model = GetInfoFromIdentifiersResp(
            results=info_responses, errors=list(id_triple_resp.errors.values())
        )
        return resp_model.model_dump(mode="json")
