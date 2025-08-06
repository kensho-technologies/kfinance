from textwrap import dedent
from typing import Type

from pydantic import BaseModel, Field

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.fetch import KFinanceApiClient
from kfinance.client.permission_models import Permission
from kfinance.domains.companies.company_identifiers import (
    CompanyIdentifier,
    fetch_company_ids_from_identifiers,
    parse_identifiers,
)
from kfinance.domains.earnings.earning_models import EarningsCallResp
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
)


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

    def _run(self, identifiers: list[str]) -> dict:
        """Sample response:

        {
            'SPGI': [
                {
                    'datetime': '2025-04-29T12:30:00Z',
                    'key_dev_id': 12346,
                    'name': 'SPGI Q1 2025 Earnings Call'
                }
            ]
        }

        """
        earnings_responses = get_earnings_from_identifiers(
            identifiers=identifiers, kfinance_api_client=self.kfinance_client.kfinance_api_client
        )
        return {
            str(identifier): earnings.model_dump(mode="json")["earnings_calls"]
            for identifier, earnings in earnings_responses.items()
        }


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

    def _run(self, identifiers: list[str]) -> dict:
        """Sample response:

        {
            'JPM': {
                'datetime': '2025-04-29T12:30:00Z',
                'key_dev_id': 12346,
                'name': 'SPGI Q1 2025 Earnings Call'
            },
            'SPGI': 'No latest earnings available.'
        }
        """
        earnings_responses = get_earnings_from_identifiers(
            identifiers=identifiers, kfinance_api_client=self.kfinance_client.kfinance_api_client
        )
        output = {}
        for identifier, earnings in earnings_responses.items():
            most_recent_earnings = earnings.most_recent_earnings
            if most_recent_earnings:
                identifier_output: str | dict = most_recent_earnings.model_dump(mode="json")
            else:
                identifier_output = f"No latest earnings available."
            output[str(identifier)] = identifier_output
        return output


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

    def _run(self, identifiers: list[str]) -> dict:
        """Sample response:

        {
            'JPM': {
                'datetime': '2025-04-29T12:30:00Z',
                'key_dev_id': 12346,
                'name': 'SPGI Q1 2025 Earnings Call'
            },
            'SPGI': 'No next earnings available.'
        }
        """
        earnings_responses = get_earnings_from_identifiers(
            identifiers=identifiers, kfinance_api_client=self.kfinance_client.kfinance_api_client
        )
        output = {}
        for identifier, earnings in earnings_responses.items():
            next_earnings = earnings.next_earnings
            if next_earnings:
                identifier_output: str | dict = next_earnings.model_dump(mode="json")
            else:
                identifier_output = f"No next earnings available."
            output[str(identifier)] = identifier_output
        return output


def get_earnings_from_identifiers(
    identifiers: list[str], kfinance_api_client: KFinanceApiClient
) -> dict[CompanyIdentifier, EarningsCallResp]:
    """Return the earnings call response for all passed identifiers."""

    parsed_identifiers = parse_identifiers(identifiers=identifiers, api_client=kfinance_api_client)
    identifiers_to_company_ids = fetch_company_ids_from_identifiers(
        identifiers=parsed_identifiers, api_client=kfinance_api_client
    )

    tasks = [
        Task(
            func=kfinance_api_client.fetch_earnings,
            kwargs=dict(company_id=company_id),
            result_key=identifier,
        )
        for identifier, company_id in identifiers_to_company_ids.items()
    ]

    earnings_responses = process_tasks_in_thread_pool_executor(
        api_client=kfinance_api_client, tasks=tasks
    )
    return earnings_responses


class GetTranscriptFromKeyDevIdArgs(BaseModel):
    """Tool argument with a key_dev_id."""

    key_dev_id: int = Field(description="The key dev ID for the earnings call")


class GetTranscriptFromKeyDevId(KfinanceTool):
    name: str = "get_transcript_from_key_dev_id"
    description: str = "Get the raw transcript text for an earnings call by key dev ID."
    args_schema: Type[BaseModel] = GetTranscriptFromKeyDevIdArgs
    accepted_permissions: set[Permission] | None = {Permission.TranscriptsPermission}

    def _run(self, key_dev_id: int) -> str:
        transcript = self.kfinance_client.transcript(key_dev_id)
        return transcript.raw
