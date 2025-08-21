from textwrap import dedent
from typing import Type

from pydantic import BaseModel, Field

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.fetch import KFinanceApiClient
from kfinance.client.permission_models import Permission
from kfinance.domains.earnings.earning_models import EarningsCall, EarningsCallResp
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
)


class GetEarningsFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, EarningsCallResp]


class GetNextOrLatestEarningsFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, EarningsCall]


class GetEarningsFromIdentifiers(KfinanceTool):
    name: str = "get_earnings_from_identifiers"
    description: str = dedent("""
        Get all earnings for a list of identifiers.

        Returns a list of dictionaries, with 'name' (str), 'key_dev_id' (int), and 'datetime' (str in ISO 8601 format with UTC timezone) attributes for each identifier.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {
        Permission.EarningsPermission,
        Permission.TranscriptsPermission,
    }

    def _run(self, identifiers: list[str]) -> GetEarningsFromIdentifiersResp:
        """Sample response:

        {
            "results": {
                'SPGI': [
                    {
                        'datetime': '2025-04-29T12:30:00Z',
                        'key_dev_id': 12346,
                        'name': 'SPGI Q1 2025 Earnings Call'
                    }
                ]
            },
            "errors": ['No identification triple found for the provided identifier: NON-EXISTENT of type: ticker']
        }

        """
        return get_earnings_from_identifiers(
            identifiers=identifiers, kfinance_api_client=self.kfinance_client.kfinance_api_client
        )


class GetLatestEarningsFromIdentifiers(KfinanceTool):
    name: str = "get_latest_earnings_from_identifiers"
    description: str = dedent("""
        Get the latest earnings for a list of identifiers.

        Returns a dictionary with 'name' (str), 'key_dev_id' (int), and 'datetime' (str in ISO 8601 format with UTC timezone) attributes for each identifier.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {
        Permission.EarningsPermission,
        Permission.TranscriptsPermission,
    }

    def _run(self, identifiers: list[str]) -> GetNextOrLatestEarningsFromIdentifiersResp:
        """Sample response:

        {
            "results": {
                'JPM': {
                    'datetime': '2025-04-29T12:30:00Z',
                    'key_dev_id': 12346,
                    'name': 'SPGI Q1 2025 Earnings Call'
                },
            },
            "errors": ["No latest earnings available for Kensho."]
        }
        """
        earnings_responses = get_earnings_from_identifiers(
            identifiers=identifiers, kfinance_api_client=self.kfinance_client.kfinance_api_client
        )
        output_model = GetNextOrLatestEarningsFromIdentifiersResp(results=dict(), errors=list())
        for identifier, earnings in earnings_responses.results.items():
            most_recent_earnings = earnings.most_recent_earnings
            if most_recent_earnings:
                output_model.results[identifier] = most_recent_earnings
            else:
                output_model.errors.append(f"No latest earnings available for {identifier}.")
        return output_model


class GetNextEarningsFromIdentifiers(KfinanceTool):
    name: str = "get_next_earnings_from_identifiers"
    description: str = dedent("""
        Get the next earnings for a given identifier.

        Returns a dictionary with 'name' (str), 'key_dev_id' (int), and 'datetime' (str in ISO 8601 format with UTC timezone) attributes for each identifier."
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {
        Permission.EarningsPermission,
        Permission.TranscriptsPermission,
    }

    def _run(self, identifiers: list[str]) -> GetNextOrLatestEarningsFromIdentifiersResp:
        """Sample response:

        {
            "results": {
                'JPM': {
                    'datetime': '2025-04-29T12:30:00Z',
                    'key_dev_id': 12346,
                    'name': 'SPGI Q1 2025 Earnings Call'
                },
            },
            "errors": ["No next earnings available for Kensho."]
        }
        """
        earnings_responses = get_earnings_from_identifiers(
            identifiers=identifiers, kfinance_api_client=self.kfinance_client.kfinance_api_client
        )
        output_model = GetNextOrLatestEarningsFromIdentifiersResp(results=dict(), errors=list())
        for identifier, earnings in earnings_responses.results.items():
            next_earnings = earnings.next_earnings
            if next_earnings:
                output_model.results[identifier] = next_earnings
            else:
                output_model.errors.append(f"No next earnings available for {identifier}.")
        return output_model


def get_earnings_from_identifiers(
    identifiers: list[str], kfinance_api_client: KFinanceApiClient
) -> GetEarningsFromIdentifiersResp:
    """Return the earnings call response for all passed identifiers."""

    api_client = kfinance_api_client
    id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)

    tasks = [
        Task(
            func=kfinance_api_client.fetch_earnings,
            kwargs=dict(company_id=id_triple.company_id),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    earnings_responses = process_tasks_in_thread_pool_executor(
        api_client=kfinance_api_client, tasks=tasks
    )
    resp_model = GetEarningsFromIdentifiersResp(
        results=earnings_responses, errors=list(id_triple_resp.errors.values())
    )
    return resp_model


class GetTranscriptFromKeyDevIdArgs(BaseModel):
    """Tool argument with a key_dev_id."""

    key_dev_id: int = Field(description="The key dev ID for the earnings call")


class GetTranscriptFromKeyDevIdResp(BaseModel):
    transcript: str


class GetTranscriptFromKeyDevId(KfinanceTool):
    name: str = "get_transcript_from_key_dev_id"
    description: str = "Get the raw transcript text for an earnings call by key dev ID."
    args_schema: Type[BaseModel] = GetTranscriptFromKeyDevIdArgs
    accepted_permissions: set[Permission] | None = {Permission.TranscriptsPermission}

    def _run(self, key_dev_id: int) -> GetTranscriptFromKeyDevIdResp:
        transcript = self.kfinance_client.transcript(key_dev_id)
        return GetTranscriptFromKeyDevIdResp(transcript=transcript.raw)
