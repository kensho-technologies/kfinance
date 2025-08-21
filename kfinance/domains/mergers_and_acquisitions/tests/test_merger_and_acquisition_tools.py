from copy import deepcopy

from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.client.tests.test_objects import (
    MERGERS_RESP,
    ordered,
)
from kfinance.conftest import SPGI_COMPANY_ID
from kfinance.domains.mergers_and_acquisitions.merger_and_acquisition_models import (
    AdvisorResp,
    MergerInfo,
)
from kfinance.domains.mergers_and_acquisitions.merger_and_acquisition_tools import (
    GetAdvisorsForCompanyInTransactionFromIdentifier,
    GetAdvisorsForCompanyInTransactionFromIdentifierArgs,
    GetAdvisorsForCompanyInTransactionFromIdentifierResp,
    GetMergerInfoFromTransactionId,
    GetMergerInfoFromTransactionIdArgs,
    GetMergersFromIdentifiers,
    GetMergersFromIdentifiersResp,
)
from kfinance.integrations.tool_calling.tool_calling_models import ToolArgsWithIdentifiers


class TestGetMergersFromIdentifiers:
    def test_get_mergers_from_identifiers(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetMergersFromIdentifiers tool
        WHEN we request mergers for SPGI and a non-existent company
        THEN we get back the SPGI mergers and an error for the non-existent company"""

        merger_data = MERGERS_RESP.model_dump(mode="json")
        expected_response = GetMergersFromIdentifiersResp.model_validate(
            {
                "results": {"SPGI": merger_data},
                "errors": [
                    "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                ],
            }
        )
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/mergers/{SPGI_COMPANY_ID}", json=merger_data
        )
        tool = GetMergersFromIdentifiers(kfinance_client=mock_client)
        args = ToolArgsWithIdentifiers(identifiers=["SPGI", "non-existent"])
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response


class TestGetCompaniesAdvisingCompanyInTransactionFromIdentifier:
    def test_get_companies_advising_company_in_transaction_from_identifier(
        self, requests_mock: Mocker, mock_client: Client
    ):
        advisor_data = {
            "advisor_company_id": 251994106,
            "advisor_company_name": "Kensho Technologies, Inc.",
            "advisor_type_name": "Professional Mongo Enjoyer",
        }
        expected_response = GetAdvisorsForCompanyInTransactionFromIdentifierResp(
            results=[
                AdvisorResp(
                    advisor_company_id=251994106,
                    advisor_company_name="Kensho Technologies, Inc.",
                    advisor_type_name="Professional Mongo Enjoyer",
                )
            ],
            errors=[],
        )

        transaction_id = 554979212
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/merger/info/{transaction_id}/advisors/{SPGI_COMPANY_ID}",
            json={"advisors": [deepcopy(advisor_data)]},
        )
        tool = GetAdvisorsForCompanyInTransactionFromIdentifier(kfinance_client=mock_client)
        args = GetAdvisorsForCompanyInTransactionFromIdentifierArgs(
            identifier="SPGI", transaction_id=transaction_id
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_get_companies_advising_company_in_transaction_from_bad_identifier(
        self, mock_client: Client
    ):
        expected_response = GetAdvisorsForCompanyInTransactionFromIdentifierResp(
            results=[],
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )
        transaction_id = 554979212
        tool = GetAdvisorsForCompanyInTransactionFromIdentifier(kfinance_client=mock_client)
        args = GetAdvisorsForCompanyInTransactionFromIdentifierArgs(
            identifier="non-existent", transaction_id=transaction_id
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response


class TestGetMergerInfoFromTransactionId:
    def test_get_merger_info_from_transaction_id(self, requests_mock: Mocker, mock_client: Client):
        timeline_resp = [
            {"status": "Announced", "date": "2000-09-12"},
            {"status": "Closed", "date": "2000-09-12"},
        ]
        participants_resp = {
            "target": {"company_id": 31696, "company_name": "MongoMusic, Inc."},
            "buyers": [{"company_id": 21835, "company_name": "Microsoft Corporation"}],
            "sellers": [
                {"company_id": 18805, "company_name": "Angel Investors L.P."},
                {"company_id": 20087, "company_name": "Draper Richards, L.P."},
            ],
        }

        consideration_resp = {
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
        }

        expected_response = MergerInfo.model_validate(
            {
                "timeline": timeline_resp,
                "participants": participants_resp,
                "consideration": consideration_resp,
            }
        )

        transaction_id = 517414
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/merger/info/{transaction_id}",
            json={
                "timeline": timeline_resp,
                "participants": participants_resp,
                "consideration": consideration_resp,
            },
        )
        tool = GetMergerInfoFromTransactionId(kfinance_client=mock_client)
        args = GetMergerInfoFromTransactionIdArgs(transaction_id=transaction_id)
        response = tool.run(args.model_dump(mode="json"))
        assert ordered(response) == ordered(expected_response)
