import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.client.models.response_models import PostResponse
from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX
from kfinance.domains.line_items.response_notes import (
    FISCAL_PERIOD_WARNING,
    FISCAL_YEAR_TERMINOLOGY_WARNING,
)
from kfinance.domains.statements.statement_models import StatementsResp, StatementType
from kfinance.domains.statements.statement_tools import (
    GetFinancialStatementFromIdentifiersResp,
    fetch_statements_from_company_ids,
    get_financial_statement_from_identifiers,
)


class TestStatements:
    statement_resp = {
        "currency": "USD",
        "periods": {
            "CY2020": {
                "period_end_date": "2020-12-31",
                "num_months": 12,
                "statements": [
                    {
                        "name": "Income Statement",
                        "line_items": [
                            {"name": "Revenues", "value": "7442000000.000000", "sources": []},
                            {"name": "Total Revenues", "value": "7442000000.000000", "sources": []},
                        ],
                    }
                ],
            },
            "CY2021": {
                "period_end_date": "2021-12-31",
                "num_months": 12,
                "statements": [
                    {
                        "name": "Income Statement",
                        "line_items": [
                            {"name": "Revenues", "value": "8243000000.000000", "sources": []},
                            {"name": "Total Revenues", "value": "8243000000.000000", "sources": []},
                        ],
                    }
                ],
            },
        },
    }

    @pytest.fixture
    def add_spgi_statements_mock_resp(self, httpx_mock: HTTPXMock) -> None:
        """Add mock response for SPGI statements."""
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/statements/",
            json={"results": {str(SPGI_ID_TRIPLE.company_id): self.statement_resp}, "errors": {}},
            is_optional=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_statements_from_company_ids(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_statements_mock_resp: None,
    ) -> None:
        """
        WHEN we request SPGI's statements (using SPGI's company id)
        THEN we get back SPGI's statements
        """

        resp = await fetch_statements_from_company_ids(
            company_ids=[SPGI_ID_TRIPLE.company_id],
            statement_type=StatementType.income_statement.value,
            httpx_client=httpx_client,
        )

        expected_resp_data = {
            "results": {str(SPGI_ID_TRIPLE.company_id): self.statement_resp},
            "errors": {},
        }
        expected_resp = PostResponse[StatementsResp].model_validate(expected_resp_data)

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_financial_statement_from_identifiers(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_statements_mock_resp: None,
    ) -> None:
        """
        WHEN we request statements for SPGI and a non-existent company
        THEN we get back statements for SPGI and an error for the non-existent company
        """

        expected_resp = GetFinancialStatementFromIdentifiersResp(
            results={"SPGI": StatementsResp.model_validate(self.statement_resp)},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
            notes=[FISCAL_PERIOD_WARNING, FISCAL_YEAR_TERMINOLOGY_WARNING],
        )

        resp = await get_financial_statement_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            statement=StatementType.income_statement,
            httpx_client=httpx_client,
        )

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_most_recent_request(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN we request most recent statements for multiple companies
        THEN we only get back the most recent statement for each company
        """

        company_ids = [1, 2]

        # Mock the statements response for both companies
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/statements/",
            json={"results": {"1": self.statement_resp, "2": self.statement_resp}, "errors": {}},
        )

        expected_single_company_response = StatementsResp.model_validate(
            {
                "currency": "USD",
                "periods": {
                    "CY2021": {
                        "period_end_date": "2021-12-31",
                        "num_months": 12,
                        "statements": self.statement_resp["periods"]["CY2021"]["statements"],
                    }
                },
            }
        )

        expected_response = GetFinancialStatementFromIdentifiersResp(
            results={
                "C_1": expected_single_company_response,
                "C_2": expected_single_company_response,
            },
            notes=[FISCAL_PERIOD_WARNING, FISCAL_YEAR_TERMINOLOGY_WARNING],
        )

        resp = await get_financial_statement_from_identifiers(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            statement=StatementType.income_statement,
            httpx_client=httpx_client,
        )

        assert resp == expected_response

    @pytest.mark.asyncio
    async def test_all_identifiers_fail_resolution(
        self,
        httpx_client: httpx.AsyncClient,
    ) -> None:
        """
        WHEN all identifiers fail resolution
        THEN we get back an empty results dict and errors without calling the statements API
        """

        expected_resp = GetFinancialStatementFromIdentifiersResp(
            results={},
            errors=[
                "No identification triple found for the provided identifier:"
                " NON-EXISTENT of type: ticker"
            ],
            notes=[FISCAL_PERIOD_WARNING, FISCAL_YEAR_TERMINOLOGY_WARNING],
        )

        resp = await get_financial_statement_from_identifiers(
            identifiers=["non-existent"],
            statement=StatementType.income_statement,
            httpx_client=httpx_client,
        )

        assert resp == expected_resp
