from datetime import date
from textwrap import dedent
from typing import Type

import httpx
from pydantic import BaseModel, Field

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
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
        description="The start date for historical price retrieval. Use null for latest values. For annual queries (e.g., 'prices in 2020'), use January 1st of the year.",
        default=None,
    )
    end_date: date | None = Field(
        description="The end date for historical price retrieval. Use null for latest values. For annual queries (e.g., 'prices in 2020'), use December 31st of the year.",
        default=None,
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
        - When requesting the most recent values, leave start_date and end_date null.
        - For annual queries (e.g., "prices in 2020"), use the full year range from January 1st to December 31st.
        - If requesting prices for long periods of time (e.g., multiple years), consider using a coarser periodicity (e.g., weekly or monthly) to reduce the amount of data returned.

        Examples:
        Query: "What are the prices of Facebook and Google?"
        Function: get_prices_from_identifiers(identifiers=["Facebook", "Google"], start_date=null, end_date=null)

        Query: "Get prices for META and GOOGL"
        Function: get_prices_from_identifiers(identifiers=["META", "GOOGL"], start_date=null, end_date=null)

        Query: "How did Meta's stock perform in 2020?"
        Function: get_prices_from_identifiers(identifiers=["Meta"], start_date="2020-01-01", end_date="2020-12-31", periodicity="day")
    """).strip()
    args_schema: Type[BaseModel] = GetPricesFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.PricingPermission}

    async def _arun(
        self,
        identifiers: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
        periodicity: Periodicity = Periodicity.day,
        adjusted: bool = True,
    ) -> GetPricesFromIdentifiersResp:
        """"""
        return await get_prices_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
            start_date=start_date,
            end_date=end_date,
            periodicity=periodicity,
            adjusted=adjusted,
        )


class GetHistoryMetadataFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, HistoryMetadataResp]


class GetHistoryMetadataFromIdentifiers(KfinanceTool):
    name: str = "get_history_metadata_from_identifiers"
    description: str = dedent("""
        Get the history metadata associated with a list of identifiers. History metadata includes currency, symbol, exchange name, instrument type, and first trade date.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.

        Examples:
        Query: "What exchange does Starbucks trade on?"
        Function: get_history_metadata_from_identifiers(identifiers=["Starbucks"])

    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = None

    async def _arun(self, identifiers: list[str]) -> GetHistoryMetadataFromIdentifiersResp:
        """"""
        return await get_history_metadata_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def get_prices_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
    start_date: date | None = None,
    end_date: date | None = None,
    periodicity: Periodicity = Periodicity.day,
    adjusted: bool = True,
) -> GetPricesFromIdentifiersResp:
    """Fetch price history for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    id_triple_resp.filter_out_companies_without_trading_item_ids()
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_price_history_from_trading_item_id,
            kwargs=dict(
                trading_item_id=id_triple.trading_item_id,
                httpx_client=httpx_client,
                start_date=start_date,
                end_date=end_date,
                periodicity=periodicity,
                adjusted=adjusted,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, PriceHistory] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            results[task.result_key] = task.result

    # If we return results for more than one company and the start and end dates are unset,
    # truncate data to only return the most recent datapoint.
    if len(results) > 1 and start_date is None and end_date is None:
        for price_response in results.values():
            price_response.prices = price_response.prices[-1:]

    return GetPricesFromIdentifiersResp(results=results, errors=errors)


async def fetch_price_history_from_trading_item_id(
    trading_item_id: int,
    httpx_client: httpx.AsyncClient,
    start_date: date | None = None,
    end_date: date | None = None,
    periodicity: Periodicity = Periodicity.day,
    adjusted: bool = True,
) -> PriceHistory:
    """Fetch price history for one trading_item_id."""
    start_date_str = start_date.isoformat() if start_date else "none"
    end_date_str = end_date.isoformat() if end_date else "none"
    adjusted_str = "adjusted" if adjusted else "unadjusted"

    url = f"/pricing/{trading_item_id}/{start_date_str}/{end_date_str}/{periodicity.value}/{adjusted_str}"
    resp = await httpx_client.get(url=url)
    resp.raise_for_status()
    return PriceHistory.model_validate(resp.json())


async def get_history_metadata_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
) -> GetHistoryMetadataFromIdentifiersResp:
    """Fetch history metadata for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    id_triple_resp.filter_out_companies_without_trading_item_ids()
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_history_metadata_from_trading_item_id,
            kwargs=dict(
                trading_item_id=id_triple.trading_item_id,
                httpx_client=httpx_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, HistoryMetadataResp] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            results[task.result_key] = task.result

    return GetHistoryMetadataFromIdentifiersResp(results=results, errors=errors)


async def fetch_history_metadata_from_trading_item_id(
    trading_item_id: int,
    httpx_client: httpx.AsyncClient,
) -> HistoryMetadataResp:
    """Fetch history metadata for one trading_item_id."""
    url = f"/pricing/{trading_item_id}/metadata"
    resp = await httpx_client.get(url=url)
    resp.raise_for_status()
    return HistoryMetadataResp.model_validate(resp.json())
