from copy import deepcopy

import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.client.tests.test_objects import (
    MERGERS_RESP,
    ordered,
)
from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.mergers_and_acquisitions.merger_and_acquisition_models import (
    AdvisorResp,
    MergerInfo,
)
from kfinance.domains.mergers_and_acquisitions.merger_and_acquisition_tools import (
    GetAdvisorsForCompanyInTransactionFromIdentifierResp,
    GetMergersFromIdentifiersResp,
    fetch_mergers_from_company_id,
    get_advisors_for_company_in_transaction_from_identifier,
    get_merger_info_from_transaction_id,
    get_mergers_from_identifiers,
)


class TestMergersAndAcquisitions:
    @pytest.fixture
    def add_spgi_mergers_mock_resp(self, httpx_mock: HTTPXMock) -> None:
        """Add mock response for SPGI mergers."""
        merger_data = MERGERS_RESP.model_dump(mode="json")
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/mergers/{SPGI_ID_TRIPLE.company_id}",
            json=merger_data,
            is_optional=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_mergers_from_company_id(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_mergers_mock_resp: None,
    ) -> None:
        """
        WHEN we request SPGI's mergers (using SPGI's company id)
        THEN we get back SPGI's mergers
        """

        resp = await fetch_mergers_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            httpx_client=httpx_client,
        )

        expected_resp = MERGERS_RESP
        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_mergers_from_identifiers(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_mergers_mock_resp: None,
    ) -> None:
        """
        WHEN we request mergers for SPGI and a non-existent company
        THEN we get back the SPGI mergers and an error for the non-existent company
        """

        expected_resp = GetMergersFromIdentifiersResp(
            identifier_results={"SPGI": MERGERS_RESP},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )

        resp = await get_mergers_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            httpx_client=httpx_client,
        )

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_merger_info_from_transaction_id(
        self,
        httpx_client: httpx.AsyncClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """
        WHEN we request merger info for a specific transaction
        THEN we get back the detailed merger information
        """
        transaction_id = 517414

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

        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/merger/info/{transaction_id}",
            json={
                "timeline": timeline_resp,
                "participants": participants_resp,
                "consideration": consideration_resp,
            },
        )

        expected_response = MergerInfo.model_validate(
            {
                "timeline": timeline_resp,
                "participants": participants_resp,
                "consideration": consideration_resp,
            }
        )

        resp = await get_merger_info_from_transaction_id(
            transaction_id=transaction_id,
            httpx_client=httpx_client,
        )

        assert ordered(resp) == ordered(expected_response)

    @pytest.mark.asyncio
    async def test_get_advisors_for_company_in_transaction_from_identifier(
        self,
        httpx_client: httpx.AsyncClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """
        WHEN we request advisors for a company in a specific transaction
        THEN we get back the advisor information
        """
        transaction_id = 554979212

        advisor_data = {
            "advisor_company_id": 251994106,
            "advisor_company_name": "Kensho Technologies, Inc.",
            "advisor_type_name": "Professional Mongo Enjoyer",
        }

        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/merger/info/{transaction_id}/advisors/{SPGI_ID_TRIPLE.company_id}",
            json={"advisors": [deepcopy(advisor_data)]},
        )

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

        resp = await get_advisors_for_company_in_transaction_from_identifier(
            identifier="SPGI",
            transaction_id=transaction_id,
            httpx_client=httpx_client,
        )

        assert resp == expected_response

    @pytest.mark.asyncio
    async def test_get_advisors_for_company_in_transaction_from_bad_identifier(
        self,
        httpx_client: httpx.AsyncClient,
    ) -> None:
        """
        WHEN we request advisors for a non-existent company identifier
        THEN we get back an error
        """
        transaction_id = 554979212

        expected_response = GetAdvisorsForCompanyInTransactionFromIdentifierResp(
            results=[],
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )

        resp = await get_advisors_for_company_in_transaction_from_identifier(
            identifier="non-existent",
            transaction_id=transaction_id,
            httpx_client=httpx_client,
        )

        assert resp == expected_response
