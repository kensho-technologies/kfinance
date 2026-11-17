from textwrap import dedent
from typing import Any, Type

import httpx2
from pydantic import BaseModel, Field

from kfinance.client.permission_models import Permission
from kfinance.integrations.tool_calling.tool_calling_models import KfinanceTool


# Company screener takes longer than a typical API request, so we set a higher timeout.
COMPANY_SCREENER_TIMEOUT_SECONDS = 60


class ScreenCompaniesWithNaturalQueryArgs(BaseModel):
    natural_language_query: str = Field(
        description="A short company screening query in natural language."
    )


class ScreenCompaniesWithNaturalQueryResp(BaseModel):
    """The screener tables, passed through as returned by the API.

    Each table has a `schema`, `data` rows, `sources`, `problems` (e.g. `unable_to_answer`
    or `results_truncated`), and `metadata`. The API caps each table at 100 rows.
    """

    response: list[dict[str, Any]]


class ScreenCompaniesWithNaturalQuery(KfinanceTool):
    name: str = "screen_companies_with_natural_query"
    description: str = dedent("""
        Use this tool if the user is asking an open ended company screening question that can't be answered with the other tools. All other tools require the companies to be known in advance. This tool can be used when the user is asking for a list of companies that satisfy a criteria.

        - Write a short natural language screening query. Do not copy the user's full prompt.
        - Answers can take up to a minute.

        Examples:
        Query: "What are the companies in the US with more than $500M revenue and with margins over 20%"
        Function: screen_companies_with_natural_query(natural_language_query="US software companies with over $500M revenue and margins above 20%")

        Query: "Give me European banks bigger than $50B in total assets"
        Function: screen_companies_with_natural_query(natural_language_query="European banks with total assets over $50B USD")
    """).strip()
    args_schema: Type[BaseModel] = ScreenCompaniesWithNaturalQueryArgs
    accepted_permissions: set[Permission] | None = {Permission.CompanyScreenerPermission}

    async def _arun(self, natural_language_query: str) -> ScreenCompaniesWithNaturalQueryResp:
        return await screen_companies_with_natural_query(
            natural_language_query=natural_language_query,
            httpx_client=self.kfinance_client.httpx_client,
        )


async def screen_companies_with_natural_query(
    natural_language_query: str, httpx_client: httpx2.AsyncClient
) -> ScreenCompaniesWithNaturalQueryResp:
    """Screen companies with a natural language query."""
    resp = await httpx_client.post(
        url="/beta/company_screener/",
        json={"natural_language_query": natural_language_query},
        timeout=COMPANY_SCREENER_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return ScreenCompaniesWithNaturalQueryResp.model_validate(resp.json())
