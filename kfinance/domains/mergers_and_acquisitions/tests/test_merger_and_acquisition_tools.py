from datetime import date

import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.client.tests.test_objects import (
    MERGERS_RESP,
    ordered,
)
from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.mergers_and_acquisitions.merger_and_acquisition_models import (
    MergersInfo,
    MergersResp,
)
from kfinance.domains.mergers_and_acquisitions.merger_and_acquisition_tools import (
    GetMergersFromIdentifiersResp,
    fetch_mergers_from_company_id,
    get_mergers_from_identifiers,
    get_mergers_info_from_transaction_ids,
)


class TestMergersAndAcquisitions:
    @pytest.fixture
    def add_spgi_mergers_mock_resp(self, httpx_mock: HTTPXMock) -> None:
        """Add mock response for SPGI mergers."""
        merger_data = MERGERS_RESP.model_dump(mode="json")
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/mergers/{SPGI_ID_TRIPLE.company_id}/none/none",
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
    async def test_fetch_mergers_from_company_id_with_date_range(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN we request SPGI's mergers for a specific date range,
        THEN we get back only those mergers
        """
        start_date = date(2022, 1, 1)
        end_date = date(2024, 5, 1)

        # We're just using a different response than the previous test here - the actual filtering doesn't matter.
        expected_resp = MergersResp(
            target=[MERGERS_RESP.target[0]],
            buyer=[MERGERS_RESP.buyer[0]],
            seller=[MERGERS_RESP.seller[0]],
        )

        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/mergers/{SPGI_ID_TRIPLE.company_id}/{start_date.isoformat()}/{end_date.isoformat()}",
            json=expected_resp.model_dump(mode="json", by_alias=True),
        )

        resp = await fetch_mergers_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            httpx_client=httpx_client,
            start_date=start_date,
            end_date=end_date,
        )

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
            identifier_info={"SPGI": SPGI_ID_TRIPLE},
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
    async def test_get_mergers_info_from_transaction_ids(
        self,
        httpx_client: httpx.AsyncClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """
        WHEN we request merger info for multiple transactions
        THEN we get back the detailed merger information for each of them
        """
        transaction_id = 517414
        error_transaction_id = 0

        timeline_resp = [
            {"status": "Announced", "date": "2000-09-12"},
            {"status": "Closed", "date": "2000-09-12"},
        ]
        participants_resp = {
            "target": {
                "company_id": 31696,
                "company_name": "MongoMusic, Inc.",
                "percent_ownership": None,
                "advisors": [],
            },
            "buyers": [
                {
                    "company_id": 21835,
                    "company_name": "Microsoft Corporation",
                    "percent_ownership": "100.00",
                    "advisors": [],
                }
            ],
            "sellers": [
                {
                    "company_id": 18805,
                    "company_name": "Angel Investors L.P.",
                    "percent_ownership": None,
                    "advisors": [],
                },
                {
                    "company_id": 20087,
                    "company_name": "Draper Richards, L.P.",
                    "percent_ownership": None,
                    "advisors": [],
                },
            ],
        }
        consideration_resp = {
            "currency_name": "US Dollar",
            "current_calculated_gross_total_transaction_value": "51609375.000000",
            "current_calculated_implied_equity_value": "51609375.000000",
            "current_calculated_implied_enterprise_value": "51609375.000000",
            "presentation_gross_total_transaction_value": "51609375.000000",
            "presentation_implied_equity_value": "51609375.000000",
            "presentation_implied_enterprise_value": "51609375.000000",
            "target_stock_premium_1_day_prior": None,
            "target_stock_premium_7_days_prior": None,
            "target_stock_premium_30_days_prior": None,
            "current_calculated_tev_ebit": None,
            "current_calculated_tev_ebitda": None,
            "current_calculated_tev_revenues": None,
            "current_calculated_equity_net_income": None,
            "presentation_tev_ebit": None,
            "presentation_tev_ebitda": None,
            "presentation_tev_revenues": None,
            "presentation_equity_net_income": None,
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
        details_resp = {
            "buy_side_termination_fee": None,
            "sell_side_termination_fee": None,
            "comment": "Microsoft Corp. (Nasdaq: MSFT) acquired MongoMusic Inc. for approximately $51.6 million in stock on October 12, 2000.",
        }

        error_resp = f"No merger found for transaction_id: {error_transaction_id}"

        httpx_mock.add_response(
            method="POST",
            url=f"https://kfinance.kensho.com/api/v1/mergers/info",
            match_json={
                "transaction_ids": [transaction_id, error_transaction_id],
                "include_advisors": True,
                "include_comments": True,
            },
            json={
                "results": {
                    transaction_id: {
                        "timeline": timeline_resp,
                        "participants": participants_resp,
                        "consideration": consideration_resp,
                        "details": details_resp,
                    },
                    error_transaction_id: {"error": error_resp},
                }
            },
        )

        expected_response = MergersInfo.model_validate(
            {
                "results": {
                    transaction_id: {
                        "timeline": timeline_resp,
                        "participants": participants_resp,
                        "consideration": consideration_resp,
                        "details": details_resp,
                    },
                    error_transaction_id: {"error": error_resp},
                }
            }
        )

        resp = await get_mergers_info_from_transaction_ids(
            transaction_ids=[transaction_id, error_transaction_id],
            include_advisors=True,
            include_comments=True,
            httpx_client=httpx_client,
        )

        assert ordered(resp) == ordered(expected_response)
