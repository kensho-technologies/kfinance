from copy import deepcopy

from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.client.tests.test_objects import MOCK_COMPANY_DB, ordered
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX
from kfinance.domains.mergers_and_acquisitions.merger_and_acquisition_tools import (
    GetAdvisorsForCompanyInTransactionFromIdentifier,
    GetAdvisorsForCompanyInTransactionFromIdentifierArgs,
    GetMergerInfoFromTransactionId,
    GetMergerInfoFromTransactionIdArgs,
    GetMergersFromIdentifier,
)
from kfinance.integrations.tool_calling.tool_calling_models import ToolArgsWithIdentifiers


class TestGetMergersFromIdentifiers:
    def test_get_mergers_from_identifiers(self, requests_mock: Mocker, mock_client: Client):
        msft_mergers = MOCK_COMPANY_DB["21835"]["mergers"]
        expected_response = {"MSFT": msft_mergers}
        company_id = 21835
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/mergers/{company_id}", json=msft_mergers
        )
        tool = GetMergersFromIdentifier(kfinance_client=mock_client)
        args = ToolArgsWithIdentifiers(identifiers=["MSFT"])
        response = tool.run(args.model_dump(mode="json"))
        assert ordered(response) == ordered(expected_response)


class TestGetCompaniesAdvisingCompanyInTransactionFromIdentifier:
    def test_get_companies_advising_company_in_transaction_from_identifier(
        self, requests_mock: Mocker, mock_client: Client
    ):
        api_response = {
            "advisors": [
                {
                    "advisor_company_id": 251994106,
                    "advisor_company_name": "Kensho Technologies, Inc.",
                    "advisor_type_name": "Professional Mongo Enjoyer",
                }
            ]
        }
        expected_response = deepcopy(api_response)
        expected_response["advisors"][0]["advisor_company_id"] = f"{COMPANY_ID_PREFIX}251994106"
        transaction_id = 517414
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/merger/info/{transaction_id}/advisors/21835",
            json=api_response,
        )
        tool = GetAdvisorsForCompanyInTransactionFromIdentifier(kfinance_client=mock_client)
        args = GetAdvisorsForCompanyInTransactionFromIdentifierArgs(
            identifier="MSFT", transaction_id=transaction_id
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response["advisors"]


class TestGetMergerInfoFromTransactionId:
    def test_get_merger_info_from_transaction_id(self, requests_mock: Mocker, mock_client: Client):
        response_base = {
            "timeline": [
                {"status": "Announced", "date": "2000-09-12"},
                {"status": "Closed", "date": "2000-09-12"},
            ],
            "participants": {},
            "consideration": {
                "currency_name": "US Dollar",
                "current_calculated_gross_total_transaction_value": "51609375.000000",
                "current_calculated_implied_equity_value": "51609375.000000",
                "current_calculated_implied_enterprise_value": "51609375.000000",
                "details": [
                    {
                        "scenario": "Stock Lump Sum",
                        "subtype": "Common Equity",
                        "cash_or_cash_equivalent_per_target_share_unit": None,
                        "number_of_target_shares_sought": "1000000.000000",
                        "current_calculated_gross_value_of_consideration": "51609375.000000",
                    }
                ],
            },
        }

        participants_api_response = {
            "target": {"company_id": 31696, "company_name": "MongoMusic, Inc."},
            "buyers": [{"company_id": 21835, "company_name": "Microsoft Corporation"}],
            "sellers": [
                {"company_id": 18805, "company_name": "Angel Investors L.P."},
                {"company_id": 20087, "company_name": "Draper Richards, L.P."},
            ],
        }
        api_response = deepcopy(response_base)
        api_response["participants"] = participants_api_response

        # Returned company IDs should be prefixed
        expected_participants_tool_response = {
            "target": {
                "company_id": f"{COMPANY_ID_PREFIX}31696",
                "company_name": "MongoMusic, Inc.",
            },
            "buyers": [
                {"company_id": f"{COMPANY_ID_PREFIX}21835", "company_name": "Microsoft Corporation"}
            ],
            "sellers": [
                {"company_id": f"{COMPANY_ID_PREFIX}18805", "company_name": "Angel Investors L.P."},
                {
                    "company_id": f"{COMPANY_ID_PREFIX}20087",
                    "company_name": "Draper Richards, L.P.",
                },
            ],
        }
        expected_response = deepcopy(response_base)
        expected_response["participants"] = expected_participants_tool_response

        transaction_id = 517414
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/merger/info/{transaction_id}",
            json=api_response,
        )
        tool = GetMergerInfoFromTransactionId(kfinance_client=mock_client)
        args = GetMergerInfoFromTransactionIdArgs(transaction_id=transaction_id)
        response = tool.run(args.model_dump(mode="json"))
        assert ordered(response) == ordered(expected_response)
