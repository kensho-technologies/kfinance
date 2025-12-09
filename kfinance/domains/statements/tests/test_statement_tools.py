from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX
from kfinance.domains.statements.statement_models import StatementType
from kfinance.domains.statements.statement_tools import (
    GetFinancialStatementFromIdentifiers,
    GetFinancialStatementFromIdentifiersArgs,
    GetFinancialStatementFromIdentifiersResp,
)


class TestGetFinancialStatementFromIdentifiers:
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

    def test_get_financial_statement_from_identifiers(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN the GetFinancialLineItemFromIdentifiers tool
        WHEN we request the income statement for SPGI and a non-existent company
        THEN we get back the SPGI income statement and an error for the non-existent company.
        """

        requests_mock.post(
            url="https://kfinance.kensho.com/api/v1/statements/",
            json=self.statement_resp,
        )
        expected_response = GetFinancialStatementFromIdentifiersResp.model_validate(
            {
                "results": {
                    "SPGI": {
                        "currency": "USD",
                        "periods": {
                            "CY2020": {
                                "period_end_date": "2020-12-31",
                                "num_months": 12,
                                "statements": [
                                    {
                                        "name": "Income Statement",
                                        "line_items": [
                                            {
                                                "name": "Revenues",
                                                "value": "7442000000.000000",
                                                "sources": [],
                                            },
                                            {
                                                "name": "Total Revenues",
                                                "value": "7442000000.000000",
                                                "sources": [],
                                            },
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
                                            {
                                                "name": "Revenues",
                                                "value": "8243000000.000000",
                                                "sources": [],
                                            },
                                            {
                                                "name": "Total Revenues",
                                                "value": "8243000000.000000",
                                                "sources": [],
                                            },
                                        ],
                                    }
                                ],
                            },
                        },
                    }
                },
                "errors": [
                    "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                ],
            }
        )

        tool = GetFinancialStatementFromIdentifiers(kfinance_client=mock_client)
        args = GetFinancialStatementFromIdentifiersArgs(
            identifiers=["SPGI", "non-existent"], statement=StatementType.income_statement
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetFinancialStatementFromIdentifiers tool
        WHEN we request most recent statement for multiple companies
        THEN we only get back the most recent statement for each company
        """

        company_ids = [1, 2]
        expected_response = GetFinancialStatementFromIdentifiersResp.model_validate(
            {
                "results": {
                    "C_1": {
                        "currency": "USD",
                        "periods": {
                            "CY2021": {
                                "period_end_date": "2021-12-31",
                                "num_months": 12,
                                "statements": [
                                    {
                                        "name": "Income Statement",
                                        "line_items": [
                                            {
                                                "name": "Revenues",
                                                "value": "8243000000.000000",
                                                "sources": [],
                                            },
                                            {
                                                "name": "Total Revenues",
                                                "value": "8243000000.000000",
                                                "sources": [],
                                            },
                                        ],
                                    }
                                ],
                            }
                        },
                    },
                    "C_2": {
                        "currency": "USD",
                        "periods": {
                            "CY2021": {
                                "period_end_date": "2021-12-31",
                                "num_months": 12,
                                "statements": [
                                    {
                                        "name": "Income Statement",
                                        "line_items": [
                                            {
                                                "name": "Revenues",
                                                "value": "8243000000.000000",
                                                "sources": [],
                                            },
                                            {
                                                "name": "Total Revenues",
                                                "value": "8243000000.000000",
                                                "sources": [],
                                            },
                                        ],
                                    }
                                ],
                            }
                        },
                    },
                }
            }
        )

        requests_mock.post(
            url="https://kfinance.kensho.com/api/v1/statements/",
            json=self.statement_resp,
        )

        tool = GetFinancialStatementFromIdentifiers(kfinance_client=mock_client)
        args = GetFinancialStatementFromIdentifiersArgs(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            statement=StatementType.income_statement,
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_empty_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetFinancialStatementFromIdentifiers tool
        WHEN we request most recent statement for multiple companies
        THEN we only get back the most recent statement for each company
        UNLESS no statements exist
        """

        company_ids = [1, 2]
        expected_response = GetFinancialStatementFromIdentifiersResp.model_validate(
            {
                "results": {
                    "C_1": {"currency": "USD", "periods": {}},
                    "C_2": {
                        "currency": "USD",
                        "periods": {
                            "CY2021": {
                                "period_end_date": "2021-12-31",
                                "num_months": 12,
                                "statements": [
                                    {
                                        "name": "Income Statement",
                                        "line_items": [
                                            {
                                                "name": "Revenues",
                                                "value": "8243000000.000000",
                                                "sources": [],
                                            },
                                            {
                                                "name": "Total Revenues",
                                                "value": "8243000000.000000",
                                                "sources": [],
                                            },
                                        ],
                                    }
                                ],
                            }
                        },
                    },
                }
            }
        )

        # Mock responses for different company requests - response depends on request_body
        def match_company_id(request, context):
            if request.json().get("company_ids") == [1]:
                return {"currency": "USD", "periods": {}}
            elif request.json().get("company_ids") == [2]:
                return self.statement_resp
            else:
                return {"currency": "USD", "periods": {}}

        requests_mock.post(
            url="https://kfinance.kensho.com/api/v1/statements/",
            json=match_company_id,
        )

        tool = GetFinancialStatementFromIdentifiers(kfinance_client=mock_client)
        args = GetFinancialStatementFromIdentifiersArgs(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            statement=StatementType.income_statement,
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response
