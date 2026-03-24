from decimal import Decimal

import httpx
from httpx import HTTPStatusError
import pytest
from pytest_httpx import HTTPXMock

from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX
from kfinance.domains.rounds_of_funding.rounds_of_funding_models import (
    AdvisorResp,
    CompanyIdAndNameWithAdvisors,
    FundingSummary,
    InvestorInRoundOfFundingWithAdvisors,
    RoundOfFundingInfoSecurity,
    RoundOfFundingInfoTimeline,
    RoundOfFundingInfoTransaction,
    RoundOfFundingInfoWithAdvisors,
    RoundOfFundingParticipantsWithAdvisors,
    RoundsOfFundingResp,
    RoundsOfFundingRole,
)
from kfinance.domains.rounds_of_funding.rounds_of_funding_tools import (
    GetFundingSummaryFromIdentifiersResp,
    GetRoundsOfFundingFromIdentifiersResp,
    GetRoundsOfFundingInfoFromTransactionIdsResp,
    fetch_rounds_of_funding_from_company_id,
    get_funding_summary_from_identifiers,
    get_rounds_of_funding_from_identifiers,
    get_rounds_of_funding_info_from_transaction_ids,
)


class TestRoundsOfFunding:
    funding_round_response = {
        "timeline": {
            "announced_date": "2023-01-15",
            "closed_date": "2023-02-15",
        },
        "participants": {
            "target": {
                "company_id": 12345,
                "company_name": "Target Company Inc.",
            },
            "investors": [
                {
                    "company_id": 67890,
                    "company_name": "Investor LLC",
                    "lead_investor": True,
                    "investment_value": "2500000.00000000",
                    "currency": "USD",
                    "ownership_percentage_pre": "0.0000",
                    "ownership_percentage_post": "15.5000",
                    "board_seat_granted": True,
                },
                {
                    "company_id": 98765,
                    "company_name": "Secondary Investor Corp",
                    "lead_investor": False,
                    "investment_value": "1000000.00000000",
                    "currency": "USD",
                    "ownership_percentage_pre": "0.0000",
                    "ownership_percentage_post": "6.2000",
                    "board_seat_granted": False,
                },
            ],
        },
        "transaction": {
            "funding_type": "Series A",
            "amount_offered": "5000000.00000000",
            "currency": "USD",
            "pre_money_valuation": "25000000.00000000",
            "post_money_valuation": "30000000.00000000",
            "use_of_proceeds": "Product development and market expansion",
            "aggregate_amount_raised": "5000000.00000000",
        },
        "security": {
            "security_description": "Series A Preferred Stock",
            "seniority_level": "Senior",
        },
    }

    rounds_of_funding_response = {
        "rounds_of_funding": [
            {
                "transaction_id": 123456,
                "funding_round_notes": "Series A funding round",
                "closed_date": "2023-02-15",
                "funding_type": "Series A",
            }
        ]
    }

    # Different transaction ID for funding summary test to avoid mock conflicts
    funding_summary_rounds_response = {
        "rounds_of_funding": [
            {
                "transaction_id": 789012,
                "funding_round_notes": "Series A funding round for summary test",
                "closed_date": "2023-02-15",
                "funding_type": "Series A",
            }
        ]
    }

    target_advisors_response = {
        "advisors": [
            {
                "advisor_company_id": 11111,
                "advisor_company_name": "Legal Advisors LLP",
                "advisor_type_name": "Legal Counsel",
                "advisor_fee_amount": 75000.0,
                "advisor_fee_currency": "USD",
                "is_lead": True,
            },
            {
                "advisor_company_id": 22222,
                "advisor_company_name": "Investment Bank Inc",
                "advisor_type_name": "Financial Advisor",
                "advisor_fee_amount": 250000.0,
                "advisor_fee_currency": "USD",
                "is_lead": True,
            },
        ]
    }

    investor_advisors_response = {
        "advisors": [
            {
                "advisor_company_id": 33333,
                "advisor_company_name": "Due Diligence Experts",
                "advisor_type_name": "Technical Advisor",
                "advisor_fee_amount": 50000.0,
                "advisor_fee_currency": "EUR",
                "is_lead": False,
            }
        ]
    }

    @pytest.fixture
    def add_spgi_rounds_mock_resp(self, httpx_mock: HTTPXMock) -> None:
        """Add mock response for SPGI rounds of funding."""
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/fundingrounds/target/{SPGI_ID_TRIPLE.company_id}",
            json=self.rounds_of_funding_response,
            is_optional=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_rounds_of_funding_from_company_id(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_rounds_mock_resp: None,
    ) -> None:
        """
        WHEN we request SPGI's rounds of funding (using SPGI's company id)
        THEN we get back SPGI's rounds of funding
        """

        resp = await fetch_rounds_of_funding_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            role=RoundsOfFundingRole.company_raising_funds,
            httpx_client=httpx_client,
        )

        expected_resp = RoundsOfFundingResp.model_validate(self.rounds_of_funding_response)
        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_rounds_of_funding_from_identifiers(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_rounds_mock_resp: None,
    ) -> None:
        """
        WHEN we request rounds of funding for SPGI and a non-existent company
        THEN we get back rounds of funding for SPGI and an error for the non-existent company
        """

        expected_resp = GetRoundsOfFundingFromIdentifiersResp(
            results={"SPGI": RoundsOfFundingResp.model_validate(self.rounds_of_funding_response)},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )

        resp = await get_rounds_of_funding_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            role=RoundsOfFundingRole.company_raising_funds,
            httpx_client=httpx_client,
        )

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_rounds_of_funding_info_from_transaction_ids_complete_data(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN we request funding round info for a transaction with complete advisor data
        THEN we get back complete data including advisors
        """
        transaction_id = 123456

        expected_result = GetRoundsOfFundingInfoFromTransactionIdsResp(
            results={
                123456: RoundOfFundingInfoWithAdvisors(
                    timeline=RoundOfFundingInfoTimeline(
                        announced_date="2023-01-15",
                        closed_date="2023-02-15",
                    ),
                    participants=RoundOfFundingParticipantsWithAdvisors(
                        target=CompanyIdAndNameWithAdvisors(
                            company_id=12345,
                            company_name="Target Company Inc.",
                            advisors=[
                                AdvisorResp(
                                    advisor_company_id=11111,
                                    advisor_company_name="Legal Advisors LLP",
                                    advisor_type_name="Legal Counsel",
                                    advisor_fee_amount=75000.0,
                                    advisor_fee_currency="USD",
                                    is_lead=True,
                                ),
                                AdvisorResp(
                                    advisor_company_id=22222,
                                    advisor_company_name="Investment Bank Inc",
                                    advisor_type_name="Financial Advisor",
                                    advisor_fee_amount=250000.0,
                                    advisor_fee_currency="USD",
                                    is_lead=True,
                                ),
                            ],
                        ),
                        investors=[
                            InvestorInRoundOfFundingWithAdvisors(
                                company_id=67890,
                                company_name="Investor LLC",
                                lead_investor=True,
                                investment_value=Decimal("2500000.00000000"),
                                currency="USD",
                                ownership_percentage_pre=Decimal("0.0000"),
                                ownership_percentage_post=Decimal("15.5000"),
                                board_seat_granted=True,
                                advisors=[
                                    AdvisorResp(
                                        advisor_company_id=33333,
                                        advisor_company_name="Due Diligence Experts",
                                        advisor_type_name="Technical Advisor",
                                        advisor_fee_amount=50000.0,
                                        advisor_fee_currency="EUR",
                                        is_lead=False,
                                    ),
                                ],
                            ),
                            InvestorInRoundOfFundingWithAdvisors(
                                company_id=98765,
                                company_name="Secondary Investor Corp",
                                lead_investor=False,
                                investment_value=Decimal("1000000.00000000"),
                                currency="USD",
                                ownership_percentage_pre=Decimal("0.0000"),
                                ownership_percentage_post=Decimal("6.2000"),
                                board_seat_granted=False,
                                advisors=[],
                            ),
                        ],
                    ),
                    transaction=RoundOfFundingInfoTransaction(
                        funding_type="Series A",
                        amount_offered=Decimal("5000000.00000000"),
                        currency="USD",
                        pre_money_valuation=Decimal("25000000.00000000"),
                        post_money_valuation=Decimal("30000000.00000000"),
                        use_of_proceeds="Product development and market expansion",
                        aggregate_amount_raised=Decimal("5000000.00000000"),
                    ),
                    security=RoundOfFundingInfoSecurity(
                        security_description="Series A Preferred Stock",
                        seniority_level="Senior",
                    ),
                )
            },
            errors=[],
        )

        # Mock the main funding round API call
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}",
            json=self.funding_round_response,
        )

        # Mock advisor API calls with actual advisor data
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}/advisors/target",
            json=self.target_advisors_response,
        )
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}/advisors/investor/{67890}",
            json=self.investor_advisors_response,
        )
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}/advisors/investor/{98765}",
            json={"advisors": []},  # No advisors for this investor
        )

        result = await get_rounds_of_funding_info_from_transaction_ids(
            transaction_ids=[transaction_id],
            httpx_client=httpx_client,
        )

        assert result == expected_result

    @pytest.mark.asyncio
    async def test_get_rounds_of_funding_info_with_mixed_advisor_data(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN some advisor API calls return data and others return empty lists
        THEN we get advisors for some results and empty lists for others
        """
        transaction_id = 345678

        expected_result = GetRoundsOfFundingInfoFromTransactionIdsResp(
            results={
                345678: RoundOfFundingInfoWithAdvisors(
                    timeline=RoundOfFundingInfoTimeline(
                        announced_date="2023-01-15",
                        closed_date="2023-02-15",
                    ),
                    participants=RoundOfFundingParticipantsWithAdvisors(
                        target=CompanyIdAndNameWithAdvisors(
                            company_id=12345,
                            company_name="Target Company Inc.",
                            advisors=[],
                        ),
                        investors=[
                            InvestorInRoundOfFundingWithAdvisors(
                                company_id=67890,
                                company_name="Investor LLC",
                                lead_investor=True,
                                investment_value=Decimal("2500000.00000000"),
                                currency="USD",
                                ownership_percentage_pre=Decimal("0.0000"),
                                ownership_percentage_post=Decimal("15.5000"),
                                board_seat_granted=True,
                                advisors=[
                                    AdvisorResp(
                                        advisor_company_id=33333,
                                        advisor_company_name="Due Diligence Experts",
                                        advisor_type_name="Technical Advisor",
                                        advisor_fee_amount=50000.0,
                                        advisor_fee_currency="EUR",
                                        is_lead=False,
                                    ),
                                ],
                            ),
                            InvestorInRoundOfFundingWithAdvisors(
                                company_id=98765,
                                company_name="Secondary Investor Corp",
                                lead_investor=False,
                                investment_value=Decimal("1000000.00000000"),
                                currency="USD",
                                ownership_percentage_pre=Decimal("0.0000"),
                                ownership_percentage_post=Decimal("6.2000"),
                                board_seat_granted=False,
                                advisors=[],
                            ),
                        ],
                    ),
                    transaction=RoundOfFundingInfoTransaction(
                        funding_type="Series A",
                        amount_offered=Decimal("5000000.00000000"),
                        currency="USD",
                        pre_money_valuation=Decimal("25000000.00000000"),
                        post_money_valuation=Decimal("30000000.00000000"),
                        use_of_proceeds="Product development and market expansion",
                        aggregate_amount_raised=Decimal("5000000.00000000"),
                    ),
                    security=RoundOfFundingInfoSecurity(
                        security_description="Series A Preferred Stock",
                        seniority_level="Senior",
                    ),
                )
            },
            errors=[],
        )

        # Mock the main funding round API call
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}",
            json=self.funding_round_response,
        )

        # Mock advisor API calls - mixed results
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}/advisors/target",
            json={"advisors": []},
        )
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}/advisors/investor/{67890}",
            json=self.investor_advisors_response,  # Successful call with data
        )
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}/advisors/investor/{98765}",
            json={"advisors": []},
        )

        result = await get_rounds_of_funding_info_from_transaction_ids(
            transaction_ids=[transaction_id],
            httpx_client=httpx_client,
        )

        assert result == expected_result

    @pytest.mark.asyncio
    async def test_get_funding_summary_from_identifiers(
        self,
        httpx_client: httpx.AsyncClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """
        WHEN we request funding summary for multiple companies
        THEN we get back funding summaries with aggregate data
        """

        company_ids = [1, 2]

        # Mock the rounds of funding responses for both companies
        for company_id in company_ids:
            httpx_mock.add_response(
                method="GET",
                url=f"https://kfinance.kensho.com/api/v1/fundingrounds/target/{company_id}",
                json=self.funding_summary_rounds_response,
            )

        # Mock the detailed round info for the transaction (multiple times for multiple companies)
        for _ in range(2):  # Two companies will make this call
            httpx_mock.add_response(
                method="GET",
                url="https://kfinance.kensho.com/api/v1/fundinground/info/789012",
                json=self.funding_round_response,
            )

        expected_summary = FundingSummary(
            company_id=f"C_1",  # This will be the identifier, not the company_id
            total_capital_raised=5000000.0,
            total_capital_raised_currency="USD",
            total_rounds=1,
            first_funding_date="2023-02-15",
            most_recent_funding_date="2023-02-15",
            rounds_by_type={"Series A": 1},
            sources=[
                {
                    "notes": "total_capital_raised, total_rounds, first_funding_date, most_recent_funding_date, and rounds_by_type are derived from underlying rounds of funding data that might be non-comprehensive."
                }
            ],
        )

        expected_response = GetFundingSummaryFromIdentifiersResp(
            results={
                "C_1": expected_summary,
                "C_2": expected_summary.model_copy(update={"company_id": "C_2"}),
            },
        )

        resp = await get_funding_summary_from_identifiers(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            httpx_client=httpx_client,
        )

        assert resp == expected_response

    @pytest.mark.asyncio
    async def test_get_rounds_of_funding_info_http_400(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN the server returns a 400 for a non-existent transaction_id
        THEN raise_for_status raises HTTPStatusError
        """
        transaction_id = 99999999

        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}",
            status_code=400,
        )

        with pytest.raises(HTTPStatusError, match="400"):
            await get_rounds_of_funding_info_from_transaction_ids(
                transaction_ids=[transaction_id],
                httpx_client=httpx_client,
            )

    @pytest.mark.asyncio
    async def test_get_rounds_of_funding_info_advisor_endpoints_404(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN the advisor endpoints return 404
        THEN the round of funding info is returned with empty advisor lists
        """
        transaction_id = 111111

        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}",
            json=self.funding_round_response,
        )
        # Target advisors returns 404
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}/advisors/target",
            status_code=404,
        )
        # Investor advisors return 404
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}/advisors/investor/{67890}",
            status_code=404,
        )
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}/advisors/investor/{98765}",
            status_code=404,
        )

        expected_result = GetRoundsOfFundingInfoFromTransactionIdsResp(
            results={
                111111: RoundOfFundingInfoWithAdvisors(
                    timeline=RoundOfFundingInfoTimeline(
                        announced_date="2023-01-15",
                        closed_date="2023-02-15",
                    ),
                    participants=RoundOfFundingParticipantsWithAdvisors(
                        target=CompanyIdAndNameWithAdvisors(
                            company_id=12345,
                            company_name="Target Company Inc.",
                            advisors=[],
                        ),
                        investors=[
                            InvestorInRoundOfFundingWithAdvisors(
                                company_id=67890,
                                company_name="Investor LLC",
                                lead_investor=True,
                                investment_value=Decimal("2500000.00000000"),
                                currency="USD",
                                ownership_percentage_pre=Decimal("0.0000"),
                                ownership_percentage_post=Decimal("15.5000"),
                                board_seat_granted=True,
                                advisors=[],
                            ),
                            InvestorInRoundOfFundingWithAdvisors(
                                company_id=98765,
                                company_name="Secondary Investor Corp",
                                lead_investor=False,
                                investment_value=Decimal("1000000.00000000"),
                                currency="USD",
                                ownership_percentage_pre=Decimal("0.0000"),
                                ownership_percentage_post=Decimal("6.2000"),
                                board_seat_granted=False,
                                advisors=[],
                            ),
                        ],
                    ),
                    transaction=RoundOfFundingInfoTransaction(
                        funding_type="Series A",
                        amount_offered=Decimal("5000000.00000000"),
                        currency="USD",
                        pre_money_valuation=Decimal("25000000.00000000"),
                        post_money_valuation=Decimal("30000000.00000000"),
                        use_of_proceeds="Product development and market expansion",
                        aggregate_amount_raised=Decimal("5000000.00000000"),
                    ),
                    security=RoundOfFundingInfoSecurity(
                        security_description="Series A Preferred Stock",
                        seniority_level="Senior",
                    ),
                )
            },
            errors=[],
        )

        result = await get_rounds_of_funding_info_from_transaction_ids(
            transaction_ids=[transaction_id],
            httpx_client=httpx_client,
        )

        assert result == expected_result
