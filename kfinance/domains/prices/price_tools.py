from datetime import date
from textwrap import dedent
from typing import Type

from pydantic import BaseModel, Field

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.models.date_and_period_models import Periodicity
from kfinance.client.permission_models import Permission
from kfinance.domains.prices.price_models import HistoryMetadataResp, PriceHistory
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
)


class GetPricesFromIdentifiersArgs(ToolArgsWithIdentifiers):
    start_date: date | None = Field(
        description="The start date for historical price retrieval", default=None
    )
    end_date: date | None = Field(
        description="The end date for historical price retrieval", default=None
    )
    # no description because the description for enum fields comes from the enum docstring.
    periodicity: Periodicity = Field(default=Periodicity.day)
    adjusted: bool = Field(
        description="Whether to retrieve adjusted prices that account for corporate actions such as dividends and splits.",
        default=True,
    )


class GetPricesFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, PriceHistory]


class GetPricesFromIdentifiers(KfinanceTool):
    name: str = "get_prices_from_identifiers"
    description: str = dedent("""
        Get the historical open, high, low, and close prices, and volume of a group of identifiers between inclusive start_date and inclusive end date.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - When requesting the most recent values, leave start_date and end_date empty.

        Example:
        Query: "What are the prices of Facebook and Google?"
        Do:
            get_prices_from_identifiers(identifiers=["META", "GOOGL"])
        Don't:
            get_prices_from_identifiers(trading_item_ids=["META"])
            get_prices_from_identifiers(trading_item_ids=["GOOGL"])
    """).strip()
    args_schema: Type[BaseModel] = GetPricesFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.PricingPermission}

    def _run(
        self,
        identifiers: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
        periodicity: Periodicity = Periodicity.day,
        adjusted: bool = True,
    ) -> GetPricesFromIdentifiersResp:
        """Sample Response:

        {
            "SPGI": {
                'prices': [
                    {
                        'date': '2024-04-11',
                        'open': {'value': '424.26', 'unit': 'USD'},
                        'high': {'value': '425.99', 'unit': 'USD'},
                        'low': {'value': '422.04', 'unit': 'USD'},
                        'close': {'value': '422.92', 'unit': 'USD'},
                        'volume': {'value': '1129158', 'unit': 'Shares'}
                    },
                    {
                        'date': '2024-04-12',
                        'open': {'value': '419.23', 'unit': 'USD'},
                        'high': {'value': '421.94', 'unit': 'USD'},
                        'low': {'value': '416.45', 'unit': 'USD'},
                        'close': {'value': '417.81', 'unit': 'USD'},
                        'volume': {'value': '1182229', 'unit': 'Shares'}
                    }
                ]
            },
            'errors': ['No identification triple found for the provided identifier: NON-EXISTENT of type: ticker']
        }
        """

        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)
        id_triple_resp.filter_out_companies_without_trading_item_ids()

        tasks = [
            Task(
                func=api_client.fetch_history,
                kwargs=dict(
                    trading_item_id=id_triple.trading_item_id,
                    start_date=start_date,
                    end_date=end_date,
                    periodicity=periodicity,
                    is_adjusted=adjusted,
                ),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]

        price_responses: dict[str, PriceHistory] = process_tasks_in_thread_pool_executor(
            api_client=api_client, tasks=tasks
        )
        # If we return results for more than one company and the start and end dates are unset,
        # truncate data to only return the most recent datapoint.
        if len(price_responses) > 1 and start_date is None and end_date is None:
            for price_response in price_responses.values():
                price_response.prices = price_response.prices[-1:]

        return GetPricesFromIdentifiersResp(
            results=price_responses, errors=list(id_triple_resp.errors.values())
        )


class GetHistoryMetadataFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, HistoryMetadataResp]


class GetHistoryMetadataFromIdentifiers(KfinanceTool):
    name: str = "get_history_metadata_from_identifiers"
    description: str = dedent("""
        Get the history metadata associated with a list of identifiers. History metadata includes currency, symbol, exchange name, instrument type, and first trade date.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = None

    def _run(self, identifiers: list[str]) -> GetHistoryMetadataFromIdentifiersResp:
        """Sample response:

        {
            'results': {
                'SPGI': {
                    'currency': 'USD',
                    'exchange_name': 'NYSE',
                    'first_trade_date': '1968-01-02',
                    'instrument_type': 'Equity',
                    'symbol': 'SPGI'
                }
            },
            'errors': ['No identification triple found for the provided identifier: NON-EXISTENT of type: ticker']
        }
        """

        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)
        id_triple_resp.filter_out_companies_without_trading_item_ids()

        tasks = [
            Task(
                func=api_client.fetch_history_metadata,
                kwargs=dict(trading_item_id=id_triple.trading_item_id),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]

        history_metadata_responses: dict[str, HistoryMetadataResp] = (
            process_tasks_in_thread_pool_executor(api_client=api_client, tasks=tasks)
        )
        return GetHistoryMetadataFromIdentifiersResp(
            results=history_metadata_responses, errors=list(id_triple_resp.errors.values())
        )
