from decimal import Decimal

from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.domains.rounds_of_funding.rounds_of_funding_models import (
    AdvisorResp,
    CompanyIdAndNameWithAdvisors,
    InvestorInRoundOfFundingWithAdvisors,
    RoundOfFundingInfoSecurity,
    RoundOfFundingInfoTimeline,
    RoundOfFundingInfoTransaction,
    RoundOfFundingInfoWithAdvisors,
    RoundOfFundingParticipantsWithAdvisors,
)
from kfinance.domains.rounds_of_funding.rounds_of_funding_tools import (
    GetRoundsOfFundingInfoFromTransactionIds,
    GetRoundsOfFundingInfoFromTransactionIdsArgs,
    GetRoundsOfFundingInfoFromTransactionIdsResp,
)


class TestGetRoundsOfFundingInfoFromTransactionIds:
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
        },
        "security": {
            "security_description": "Series A Preferred Stock",
            "seniority_level": "Senior",
        },
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

    funding_round_response_2 = {
        "timeline": {
            "announced_date": "2024-03-20",
            "closed_date": "2024-04-10",
        },
        "participants": {
            "target": {
                "company_id": 54321,
                "company_name": "Second Target Company Ltd.",
            },
            "investors": [
                {
                    "company_id": 11111,
                    "company_name": "Primary Venture Capital",
                    "lead_investor": True,
                    "investment_value": "8000000.00000000",
                    "currency": "USD",
                    "ownership_percentage_pre": "0.0000",
                    "ownership_percentage_post": "25.0000",
                    "board_seat_granted": True,
                },
                {
                    "company_id": 22222,
                    "company_name": "Strategic Partner Corp",
                    "lead_investor": False,
                    "investment_value": "3000000.00000000",
                    "currency": "USD",
                    "ownership_percentage_pre": "0.0000",
                    "ownership_percentage_post": "9.3750",
                    "board_seat_granted": False,
                },
            ],
        },
        "transaction": {
            "funding_type": "Series B",
            "amount_offered": "12000000.00000000",
            "currency": "USD",
            "pre_money_valuation": "32000000.00000000",
            "post_money_valuation": "44000000.00000000",
            "use_of_proceeds": "International expansion and team scaling",
        },
        "security": {
            "security_description": "Series B Preferred Stock",
            "seniority_level": "Senior",
        },
    }

    def test_get_rounds_of_funding_info_complete_data(
        self, requests_mock: Mocker, mock_client: Client
    ):
        """
        GIVEN the GetRoundsOfFundingInfoFromTransactionIds tool
        WHEN we request funding round info for a transaction
        THEN we get back complete data
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
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}",
            json=self.funding_round_response,
        )

        # Mock advisor API calls with actual advisor data
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}/advisors/target",
            json=self.target_advisors_response,
        )
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}/advisors/investor/{67890}",
            json=self.investor_advisors_response,
        )
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}/advisors/investor/{98765}",
            json={"advisors": []},  # No advisors for this investor
        )

        tool = GetRoundsOfFundingInfoFromTransactionIds(kfinance_client=mock_client)
        args = GetRoundsOfFundingInfoFromTransactionIdsArgs(transaction_ids=[transaction_id])

        result = tool.run(args.model_dump(mode="json"))

        assert result == expected_result

    def test_get_rounds_of_funding_info_with_mixed_advisor_data(
        self, requests_mock: Mocker, mock_client: Client
    ):
        """
        GIVEN the GetRoundsOfFundingInfoFromTransactionIds tool
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
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}",
            json=self.funding_round_response,
        )

        # Mock advisor API calls - mixed results
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}/advisors/target",
            json={"advisors": []},
        )
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}/advisors/investor/{67890}",
            json=self.investor_advisors_response,  # Successful call with data
        )
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/fundinground/info/{transaction_id}/advisors/investor/{98765}",
            json={"advisors": []},
        )

        tool = GetRoundsOfFundingInfoFromTransactionIds(kfinance_client=mock_client)
        args = GetRoundsOfFundingInfoFromTransactionIdsArgs(transaction_ids=[transaction_id])

        result = tool.run(args.model_dump(mode="json"))

        assert result == expected_result

    def test_multiple_transaction_ids(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetRoundsOfFundingInfoFromTransactionIds tool
        WHEN we request multiple transaction IDs with different data
        THEN we get back corred data for all requested transactions
        """
        transaction_ids = [111111, 222222]

        # Mock API calls with different responses for each transaction
        requests_mock.get(
            url="https://kfinance.kensho.com/api/v1/fundinground/info/111111",
            json=self.funding_round_response,
        )
        requests_mock.get(
            url="https://kfinance.kensho.com/api/v1/fundinground/info/222222",
            json=self.funding_round_response_2,
        )

        # Mock advisor calls for first transaction
        requests_mock.get(
            url="https://kfinance.kensho.com/api/v1/fundinground/info/111111/advisors/target",
            json={"advisors": []},
        )
        requests_mock.get(
            url="https://kfinance.kensho.com/api/v1/fundinground/info/111111/advisors/investor/67890",
            json={"advisors": []},
        )
        requests_mock.get(
            url="https://kfinance.kensho.com/api/v1/fundinground/info/111111/advisors/investor/98765",
            json={"advisors": []},
        )

        # Mock advisor calls for second transaction
        requests_mock.get(
            url="https://kfinance.kensho.com/api/v1/fundinground/info/222222/advisors/target",
            json={"advisors": []},
        )
        requests_mock.get(
            url="https://kfinance.kensho.com/api/v1/fundinground/info/222222/advisors/investor/11111",
            json={"advisors": []},
        )
        requests_mock.get(
            url="https://kfinance.kensho.com/api/v1/fundinground/info/222222/advisors/investor/22222",
            json={"advisors": []},
        )

        tool = GetRoundsOfFundingInfoFromTransactionIds(kfinance_client=mock_client)
        args = GetRoundsOfFundingInfoFromTransactionIdsArgs(transaction_ids=transaction_ids)

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
                    ),
                    security=RoundOfFundingInfoSecurity(
                        security_description="Series A Preferred Stock",
                        seniority_level="Senior",
                    ),
                ),
                222222: RoundOfFundingInfoWithAdvisors(
                    timeline=RoundOfFundingInfoTimeline(
                        announced_date="2024-03-20",
                        closed_date="2024-04-10",
                    ),
                    participants=RoundOfFundingParticipantsWithAdvisors(
                        target=CompanyIdAndNameWithAdvisors(
                            company_id=54321,
                            company_name="Second Target Company Ltd.",
                            advisors=[],
                        ),
                        investors=[
                            InvestorInRoundOfFundingWithAdvisors(
                                company_id=11111,
                                company_name="Primary Venture Capital",
                                lead_investor=True,
                                investment_value=Decimal("8000000.00000000"),
                                currency="USD",
                                ownership_percentage_pre=Decimal("0.0000"),
                                ownership_percentage_post=Decimal("25.0000"),
                                board_seat_granted=True,
                                advisors=[],
                            ),
                            InvestorInRoundOfFundingWithAdvisors(
                                company_id=22222,
                                company_name="Strategic Partner Corp",
                                lead_investor=False,
                                investment_value=Decimal("3000000.00000000"),
                                currency="USD",
                                ownership_percentage_pre=Decimal("0.0000"),
                                ownership_percentage_post=Decimal("9.3750"),
                                board_seat_granted=False,
                                advisors=[],
                            ),
                        ],
                    ),
                    transaction=RoundOfFundingInfoTransaction(
                        funding_type="Series B",
                        amount_offered=Decimal("12000000.00000000"),
                        currency="USD",
                        pre_money_valuation=Decimal("32000000.00000000"),
                        post_money_valuation=Decimal("44000000.00000000"),
                        use_of_proceeds="International expansion and team scaling",
                    ),
                    security=RoundOfFundingInfoSecurity(
                        security_description="Series B Preferred Stock",
                        seniority_level="Senior",
                    ),
                ),
            },
            errors=[],
        )

        result = tool.run(args.model_dump(mode="json"))

        assert result == expected_result
