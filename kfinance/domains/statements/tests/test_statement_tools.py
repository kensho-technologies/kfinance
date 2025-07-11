from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_COMPANY_ID
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX
from kfinance.domains.statements.statement_models import StatementType
from kfinance.domains.statements.statement_tools import (
    GetFinancialStatementFromIdentifiers,
    GetFinancialStatementFromIdentifiersArgs,
)


class TestGetFinancialStatementFromIdentifiers:
    statement_resp = {
        "statements": {
            "2020": {"Revenues": "7442000000.000000", "Total Revenues": "7442000000.000000"},
            "2021": {"Revenues": "8243000000.000000", "Total Revenues": "8243000000.000000"},
        }
    }

    def test_get_financial_statement_from_identifiers(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN the GetFinancialLineItemFromIdentifiers tool
        WHEN we request the SPGI income statement
        THEN we get back the SPGI income statement
        """

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/statements/{SPGI_COMPANY_ID}/income_statement/none/none/none/none/none",
            json=self.statement_resp,
        )
        expected_response = {
            "SPGI": {
                "Revenues": {"2020": 7442000000.0, "2021": 8243000000.0},
                "Total Revenues": {"2020": 7442000000.0, "2021": 8243000000.0},
            }
        }

        tool = GetFinancialStatementFromIdentifiers(kfinance_client=mock_client)
        args = GetFinancialStatementFromIdentifiersArgs(
            identifiers=["SPGI"], statement=StatementType.income_statement
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetFinancialLineItemFromIdentifiers tool
        WHEN we request most recent statement for multiple companies
        THEN we only get back the most recent statement for each company
        """

        company_ids = [1, 2]
        expected_response = {
            "C_1": {"Revenues": {"2021": 8243000000.0}, "Total Revenues": {"2021": 8243000000.0}},
            "C_2": {"Revenues": {"2021": 8243000000.0}, "Total Revenues": {"2021": 8243000000.0}},
        }

        for company_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/statements/{company_id}/income_statement/none/none/none/none/none",
                json=self.statement_resp,
            )

        tool = GetFinancialStatementFromIdentifiers(kfinance_client=mock_client)
        args = GetFinancialStatementFromIdentifiersArgs(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            statement=StatementType.income_statement,
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response
