from datetime import date
from decimal import Decimal

from kfinance.domains.companies.company_models import CompanyIdAndName
from kfinance.domains.rounds_of_funding.rounds_of_funding_models import (
    AdvisorResp,
    InvestorInRoundOfFunding,
    InvestorInRoundOfFundingWithAdvisors,
    RoundOfFundingInfo,
    RoundOfFundingInfoSecurity,
    RoundOfFundingInfoTimeline,
    RoundOfFundingInfoTransaction,
    RoundOfFundingParticipants,
)


class TestCompanyIdSerialization:
    def test_investor_serialization(self) -> None:
        """
        GIVEN an InvestorInRoundOfFunding object
        WHEN we serialize it with model_dump()
        THEN the company_id should be serialized with C_ prefix due to CompanyId type
        """
        investor = InvestorInRoundOfFunding(
            company_id=12345,
            company_name="Test Company",
            lead_investor=True,
            investment_value=Decimal("1000000.00"),
            currency="USD",
            ownership_percentage_pre=Decimal("0.00"),
            ownership_percentage_post=Decimal("15.50"),
            board_seat_granted=True,
        )

        serialized = investor.model_dump()

        # Company ID should have C_ prefix when serialized
        assert serialized["company_id"] == "C_12345"
        assert serialized["company_name"] == "Test Company"
        assert serialized["lead_investor"] is True
        assert serialized["investment_value"] == Decimal("1000000.00")
        assert serialized["currency"] == "USD"
        assert serialized["ownership_percentage_pre"] == Decimal("0.00")
        assert serialized["ownership_percentage_post"] == Decimal("15.50")
        assert serialized["board_seat_granted"] is True

    def test_investor_with_advisors_serialization(self) -> None:
        """
        GIVEN an InvestorInRoundOfFundingWithAdvisors object
        WHEN we serialize it
        THEN it should include advisor data and serialize company_id with C_ prefix
        """
        advisor = AdvisorResp(
            advisor_company_id=67890,
            advisor_company_name="Advisor LLC",
            advisor_type_name="Financial Advisor",
            advisor_fee_amount=50000.0,
            advisor_fee_currency="USD",
            is_lead=True,
        )

        investor = InvestorInRoundOfFundingWithAdvisors(
            company_id=12345,
            company_name="Test Company",
            lead_investor=True,
            ownership_percentage_pre=Decimal("0.00"),
            ownership_percentage_post=Decimal("15.00"),
            advisors=[advisor],
        )

        serialized = investor.model_dump()

        # Company ID should have C_ prefix when serialized
        assert serialized["company_id"] == "C_12345"
        assert serialized["ownership_percentage_pre"] == Decimal("0.00")
        assert serialized["ownership_percentage_post"] == Decimal("15.00")
        assert len(serialized["advisors"]) == 1
        assert serialized["advisors"][0]["advisor_company_id"] == "C_67890"
        assert serialized["advisors"][0]["advisor_fee_currency"] == "USD"


class TestRoundOfFundingInfoWithAdvisors:
    def test_with_advisors_method(self) -> None:
        """
        GIVEN a RoundOfFundingInfo object
        WHEN we call with_advisors method
        THEN it should create RoundOfFundingInfoWithAdvisors with merged advisor data
        """

        target = CompanyIdAndName(company_id=12345, company_name="Target Co.")

        investor = InvestorInRoundOfFunding(
            company_id=67890,
            company_name="Investor Co.",
            lead_investor=True,
            ownership_percentage_pre=Decimal("0.00"),
            ownership_percentage_post=Decimal("20.00"),
        )

        participants = RoundOfFundingParticipants(
            target=target,
            investors=[investor],
        )

        timeline = RoundOfFundingInfoTimeline(
            announced_date=date(2023, 1, 15),
            closed_date=date(2023, 2, 15),
        )

        transaction = RoundOfFundingInfoTransaction(
            funding_type="Series A",
            amount_offered=Decimal("5000000.00"),
            currency="USD",
        )

        security = RoundOfFundingInfoSecurity(
            security_description="Preferred Stock",
        )

        round_info = RoundOfFundingInfo(
            timeline=timeline,
            participants=participants,
            transaction=transaction,
            security=security,
        )

        target_advisor = AdvisorResp(
            advisor_company_id=11111,
            advisor_company_name="Target Legal",
            advisor_type_name="Legal Counsel",
        )

        investor_advisor = AdvisorResp(
            advisor_company_id=22222,
            advisor_company_name="Investor Bank",
            advisor_type_name="Financial Advisor",
        )

        round_info_with_advisors = round_info.with_advisors(
            target_advisors=[target_advisor],
            investor_advisors={67890: [investor_advisor]},
        )

        serialized = round_info_with_advisors.model_dump()

        assert len(serialized["participants"]["target"]["advisors"]) == 1
        assert (
            serialized["participants"]["target"]["advisors"][0]["advisor_company_id"] == "C_11111"
        )

        assert len(serialized["participants"]["investors"]) == 1
        investor_data = serialized["participants"]["investors"][0]
        assert len(investor_data["advisors"]) == 1
        assert investor_data["advisors"][0]["advisor_company_id"] == "C_22222"
        assert investor_data["ownership_percentage_pre"] == Decimal("0.00")
        assert investor_data["ownership_percentage_post"] == Decimal("20.00")
        assert investor_data["company_id"] == "C_67890"

    def test_with_advisors_handles_missing_investor_advisors(self) -> None:
        """
        GIVEN a RoundOfFundingInfo with multiple investors
        WHEN we call with_advisors with missing advisor data for some investors
        THEN investors without advisor data should have empty advisor lists
        """
        target = CompanyIdAndName(company_id=12345, company_name="Target Co.")

        investor1 = InvestorInRoundOfFunding(
            company_id=67890,
            company_name="Investor 1",
            lead_investor=True,
        )

        investor2 = InvestorInRoundOfFunding(
            company_id=98765,
            company_name="Investor 2",
            lead_investor=False,
        )

        participants = RoundOfFundingParticipants(
            target=target,
            investors=[investor1, investor2],
        )

        round_info = RoundOfFundingInfo(
            timeline=RoundOfFundingInfoTimeline(),
            participants=participants,
            transaction=RoundOfFundingInfoTransaction(),
            security=RoundOfFundingInfoSecurity(),
        )

        advisor = AdvisorResp(
            advisor_company_id=11111,
            advisor_company_name="Advisor for Investor 1",
            advisor_type_name="Financial",
        )

        # Only provide advisor for investor1, not investor2
        round_info_with_advisors = round_info.with_advisors(
            target_advisors=[],
            investor_advisors={67890: [advisor]},  # Missing 98765
        )

        serialized = round_info_with_advisors.model_dump()
        investors = serialized["participants"]["investors"]

        # Find investor1 and investor2 in results
        investor1_data = next(
            investor for investor in investors if investor["company_name"] == "Investor 1"
        )
        investor2_data = next(
            investor for investor in investors if investor["company_name"] == "Investor 2"
        )

        # Investor1 should have advisors, investor2 should have empty list
        assert len(investor1_data["advisors"]) == 1
        assert len(investor2_data["advisors"]) == 0
