import httpx2
import pytest

from kfinance.domains.company_screener.company_screener_tools import (
    ScreenCompaniesWithNaturalQueryResp,
    screen_companies_with_natural_query,
)


SCREENER_RESP = {
    "response": [
        {
            "schema": {
                "fields": [
                    {"name": "companyid", "type": "integer"},
                    {"name": "companyname", "type": ["string", "null"]},
                    {"name": "revenue_usd", "type": ["number", "null"]},
                ]
            },
            "data": [
                {"companyid": 18749, "companyname": "Amazon.com, Inc.", "revenue_usd": None},
            ],
            "sources": [],
            "problems": [],
            "metadata": {
                "raw_query": None,
                "filters": [],
                "entity_ids": {},
                "company_webpages": [],
            },
        }
    ]
}


class TestScreenCompaniesWithNaturalQuery:
    @pytest.mark.asyncio
    async def test_screen_companies_with_natural_query(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock
    ) -> None:
        """
        WHEN we screen companies with a natural language query
        THEN the query is posted to the screener endpoint and its response is passed through.
        """
        query = "Which single company has the highest revenue in USD?"
        httpx2_mock.post(
            "https://kfinance.kensho.com/api/v1/beta/company_screener/",
            json={"natural_language_query": query, "max_rows": 100},
        ).respond(json=SCREENER_RESP)

        resp = await screen_companies_with_natural_query(
            natural_language_query=query, httpx_client=httpx_client
        )

        assert resp == ScreenCompaniesWithNaturalQueryResp.model_validate(SCREENER_RESP)
        # Null cells are kept in the tool output
        assert resp.model_dump(mode="json", exclude_none=True) == SCREENER_RESP

    @pytest.mark.asyncio
    async def test_screen_companies_with_natural_query_with_max_rows(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock
    ) -> None:
        """
        WHEN we screen companies with a raised max_rows
        THEN max_rows is posted to the screener endpoint.
        """
        query = "US-listed semiconductor companies with positive net income"
        httpx2_mock.post(
            "https://kfinance.kensho.com/api/v1/beta/company_screener/",
            json={"natural_language_query": query, "max_rows": 500},
        ).respond(json=SCREENER_RESP)

        resp = await screen_companies_with_natural_query(
            natural_language_query=query, max_rows=500, httpx_client=httpx_client
        )

        assert resp == ScreenCompaniesWithNaturalQueryResp.model_validate(SCREENER_RESP)
