from datetime import date
from textwrap import dedent
from typing import Type

from pydantic import BaseModel, Field

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.permission_models import Permission
from kfinance.domains.capitalizations.capitalization_models import Capitalization
from kfinance.domains.companies.company_identifiers import (
    fetch_company_ids_from_identifiers,
    parse_identifiers,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
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
    ) -> dict:
        """Sample response:

        {
            'SPGI': [
                {'date': '2024-04-10', 'market_cap': {'unit': 'USD', 'value': '132766738270.00'}},
                {'date': '2024-04-11', 'market_cap': {'unit': 'USD', 'value': '132416066761.00'}}
            ]
        }
        """
        api_client = self.kfinance_client.kfinance_api_client
        parsed_identifiers = parse_identifiers(identifiers=identifiers, api_client=api_client)
        identifiers_to_company_ids = fetch_company_ids_from_identifiers(
            identifiers=parsed_identifiers, api_client=api_client
        )

        tasks = [
            Task(
                func=api_client.fetch_market_caps_tevs_and_shares_outstanding,
                kwargs=dict(company_id=company_id, start_date=start_date, end_date=end_date),
                result_key=identifier,
            )
            for identifier, company_id in identifiers_to_company_ids.items()
        ]

        capitalization_responses = process_tasks_in_thread_pool_executor(
            api_client=api_client, tasks=tasks
        )

        return {
            str(identifier): capitalization_response.model_dump_json_single_metric(
                capitalization_metric=capitalization,
                only_include_most_recent_value=True
                if (len(identifiers) > 1 and start_date == end_date is None)
                else False,
            )
            for identifier, capitalization_response in capitalization_responses.items()
        }
