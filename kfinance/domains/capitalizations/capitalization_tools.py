from datetime import date
from textwrap import dedent
from typing import Type

from pydantic import BaseModel, Field

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.permission_models import Permission
from kfinance.domains.capitalizations.capitalization_models import Capitalization, Capitalizations
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
)


class GetCapitalizationFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    capitalization: Capitalization
    start_date: date | None = Field(
        description="The start date for historical capitalization retrieval", default=None
    )
    end_date: date | None = Field(
        description="The end date for historical capitalization retrieval", default=None
    )


class GetCapitalizationFromIdentifiersResp(ToolRespWithErrors):
    capitalization: Capitalization
    results: dict[str, Capitalizations]


class GetCapitalizationFromIdentifiers(KfinanceTool):
    name: str = "get_capitalization_from_identifiers"
    description: str = dedent("""
        Get the historical market cap, tev (Total Enterprise Value), or shares outstanding for a group of identifiers between inclusive start_date and inclusive end date.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - When requesting the most recent values, leave start_date and end_date empty.

        Example:
        Query: "What are the market caps of AAPL and WMT?"
        Function: get_capitalization_from_identifiers(capitalization=Capitalization.market_cap, identifiers=["AAPL", "WMT"])
    """).strip()
    args_schema: Type[BaseModel] = GetCapitalizationFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.PricingPermission}

    def _run(
        self,
        identifiers: list[str],
        capitalization: Capitalization,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> GetCapitalizationFromIdentifiersResp:
        """Sample response:

        {
            'capitalization': 'market_cap'
            'results': {
                'SPGI': {
                        {'date': '2024-04-10', 'market_cap': {'value': '132766738270.00', 'unit': 'USD'}},
                        {'date': '2024-04-11', 'market_cap': {'value': '132416066761.00', 'unit': 'USD'}}
                    ]
                }
            },
            'errors': ['No identification triple found for the provided identifier: NON-EXISTENT of type: ticker']
        }
        """
        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)

        tasks = [
            Task(
                func=api_client.fetch_market_caps_tevs_and_shares_outstanding,
                kwargs=dict(
                    company_id=id_triple.company_id, start_date=start_date, end_date=end_date
                ),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]

        capitalization_responses = process_tasks_in_thread_pool_executor(
            api_client=api_client, tasks=tasks
        )

        for capitalization_response in capitalization_responses.values():
            # If we return results for more than one company and the start and end dates are unset,
            # truncate data to only return the most recent datapoint.
            if len(capitalization_responses) > 1 and start_date is None and end_date is None:
                capitalization_response.capitalizations = capitalization_response.capitalizations[
                    -1:
                ]
            # Set capitalizations that were not requested to None.
            # That way, they can be skipped for serialization via `exclude_none=True`
            for daily_capitalization in capitalization_response.capitalizations:
                if capitalization is not Capitalization.market_cap:
                    daily_capitalization.market_cap = None
                if capitalization is not Capitalization.tev:
                    daily_capitalization.tev = None
                if capitalization is not Capitalization.shares_outstanding:
                    daily_capitalization.shares_outstanding = None

        return GetCapitalizationFromIdentifiersResp(
            capitalization=capitalization,
            results=capitalization_responses,
            errors=list(id_triple_resp.errors.values()),
        )
