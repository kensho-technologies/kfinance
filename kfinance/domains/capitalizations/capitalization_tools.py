from datetime import date
from textwrap import dedent
from typing import Type

import httpx
from pydantic import BaseModel, Field

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.capitalizations.capitalization_models import Capitalization, Capitalizations
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithIdInfoAndErrors,
)


class GetCapitalizationFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    capitalization: Capitalization
    start_date: date | None = Field(
        description="The start date for historical capitalization retrieval. Use null for latest values. For annual data, use January 1st of the year.",
        default=None,
    )
    end_date: date | None = Field(
        description="The end date for historical capitalization retrieval. Use null for latest values. For annual data, use December 31st of the year.",
        default=None,
    )


class GetCapitalizationFromIdentifiersResp(ToolRespWithIdInfoAndErrors[Capitalizations]):
    capitalization: Capitalization


class GetCapitalizationFromIdentifiers(KfinanceTool):
    name: str = "get_capitalization_from_identifiers"
    description: str = dedent("""
        Get the historical market cap, tev (Total Enterprise Value), or shares outstanding for a group of identifiers between inclusive start_date and inclusive end date.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - When requesting the most recent values, leave start_date and end_date null.
        - For annual data (e.g., "market cap in 2020", "FY2021 values"), use the full year range: start_date as January 1st and end_date as December 31st.
        - For "latest" or "current" values, always leave dates null to get the most recent data point.
        - Only specify date ranges when the user explicitly requests historical data over a specific period.

        Examples:
        Query: "What are the market caps of Visa and Mastercard?"
        Function: get_capitalization_from_identifiers(capitalization="market_cap", identifiers=["Visa", "Mastercard"], start_date=null, end_date=null)

        Query: "What was MDT's market cap in 2020?"
        Function: get_capitalization_from_identifiers(capitalization="market_cap", identifiers=["MDT"], start_date="2020-01-01", end_date="2020-12-31")

        Query: "Market cap trends for MSFT from Q1 2020 to Q3 2021"
        Function: get_capitalization_from_identifiers(capitalization="market_cap", identifiers=["MSFT"], start_date="2020-01-01", end_date="2021-09-30")
    """).strip()
    args_schema: Type[BaseModel] = GetCapitalizationFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.PricingPermission}

    async def _arun(
        self,
        identifiers: list[str],
        capitalization: Capitalization,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> GetCapitalizationFromIdentifiersResp:
        """"""
        return await get_capitalizations_from_identifiers(
            identifiers=identifiers,
            capitalization=capitalization,
            start_date=start_date,
            end_date=end_date,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def get_capitalizations_from_identifiers(
    identifiers: list[str],
    capitalization: Capitalization,
    start_date: date | None,
    end_date: date | None,
    httpx_client: httpx.AsyncClient,
) -> GetCapitalizationFromIdentifiersResp:
    """Fetch market_cap, tev, or shares_outstanding for all identifiers.

    Sample Response:

    {
        'capitalization': 'market_cap'
        'results': {
            'SPGI': [
                {'date': '2024-04-10', 'market_cap': {'value': '132766738270.00', 'unit': 'USD'}},
                {'date': '2024-04-11', 'market_cap': {'value': '132416066761.00', 'unit': 'USD'}}
            ]
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
            func=fetch_capitalizations_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                start_date=start_date,
                end_date=end_date,
                httpx_client=httpx_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, Capitalizations] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            capitalization_response: Capitalizations = task.result
            # If we return results for more than one company and the start and end dates are unset,
            # truncate data to only return the most recent datapoint.
            if (
                len(tasks) > 1
                and start_date is None
                and end_date is None
                and len(capitalization_response.capitalizations) > 1
            ):
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
            results[task.result_key] = capitalization_response

    return GetCapitalizationFromIdentifiersResp(
        capitalization=capitalization,
        identifier_results=results,
        identifier_info=id_triple_resp,
        errors=errors,
    )


async def fetch_capitalizations_from_company_id(
    company_id: int,
    start_date: date | None,
    end_date: date | None,
    httpx_client: httpx.AsyncClient,
) -> Capitalizations:
    """Fetch and return capitalizations for one identifier."""
    url = (
        f"/market_cap/{company_id}/"
        f"{start_date.isoformat() if start_date is not None else 'none'}/"
        f"{end_date.isoformat() if end_date is not None else 'none'}"
    )
    resp = await httpx_client.get(url=url)
    resp.raise_for_status()
    return Capitalizations.model_validate(resp.json())
