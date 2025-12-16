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

        # Mock the unified_fetch_id_triples response
        requests_mock.post(
            url="https://kfinance.kensho.com/api/v1/ids",
            json={
                "identifiers_to_id_triples": {
                    "SPGI": {
                        "company_id": 21719,
                        "security_id": 2629107,
                        "trading_item_id": 2629108,
                    }
                },
                "errors": {
                    "NON-EXISTENT": "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                },
            },
        )

        # Mock the fetch_statement response
        requests_mock.post(
            url="https://kfinance.kensho.com/api/v1/statements/",
            json={"results": {"21719": self.statement_resp}, "errors": {}},
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
            identifiers=["SPGI", "NON-EXISTENT"], statement=StatementType.income_statement
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

        # Mock the unified_fetch_id_triples response
        requests_mock.post(
            url="https://kfinance.kensho.com/api/v1/ids",
            json={
                "identifiers_to_id_triples": {
                    "C_1": {"company_id": 1, "security_id": 101, "trading_item_id": 201},
                    "C_2": {"company_id": 2, "security_id": 102, "trading_item_id": 202},
                },
                "errors": {},
            },
        )

        # Mock the fetch_statement response
        requests_mock.post(
            url="https://kfinance.kensho.com/api/v1/statements/",
            json={"results": {"1": self.statement_resp, "2": self.statement_resp}, "errors": {}},
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

        # Mock the unified_fetch_id_triples response
        requests_mock.post(
            url="https://kfinance.kensho.com/api/v1/ids",
            json={
                "identifiers_to_id_triples": {
                    "C_1": {"company_id": 1, "security_id": 101, "trading_item_id": 201},
                    "C_2": {"company_id": 2, "security_id": 102, "trading_item_id": 202},
                },
                "errors": {},
            },
        )

        # Mock the fetch_statement response with different data for different companies
        requests_mock.post(
            url="https://kfinance.kensho.com/api/v1/statements/",
            json={
                "results": {"1": {"currency": "USD", "periods": {}}, "2": self.statement_resp},
                "errors": {},
            },
        )

        tool = GetFinancialStatementFromIdentifiers(kfinance_client=mock_client)
        args = GetFinancialStatementFromIdentifiersArgs(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            statement=StatementType.income_statement,
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response
