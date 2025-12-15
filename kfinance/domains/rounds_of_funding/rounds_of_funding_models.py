from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer
from strenum import StrEnum

from kfinance.client.models.response_models import Source
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX, CompanyIdAndName


class RoundOfFunding(BaseModel):
    transaction_id: int
    funding_round_notes: str | None
    closed_date: date | None
    funding_type: str | None = None


class RoundsOfFundingResp(BaseModel):
    rounds_of_funding: list[RoundOfFunding]


class RoundOfFundingTimelineElement(BaseModel):
    status: str
    date: date


class InvestorInRoundOfFunding(BaseModel):
    company_id: int
    company_name: str
    lead_investor: bool
    investment_value: Decimal | None = None
    currency: str | None = None

    @field_serializer("company_id")
    def serialize_with_prefix(self, company_id: int) -> str:
        """Serialize the investor company_id with a prefix ("C_<company_id>").

        Including the prefix allows us to distinguish tickers and company_ids.
        """
        return f"{COMPANY_ID_PREFIX}{company_id}"


class RoundsOfFundingRole(StrEnum):
    """The role of the company involved in the round of funding"""

    company_raising_funds = "company_raising_funds"
    company_investing_in_round_of_funding = "company_investing_in_round_of_funding"


class AdvisedCompanyRole(StrEnum):
    """The role of the company being advised in a funding round"""

    target = "target"
    investor = "investor"


class RoundOfFundingParticipants(BaseModel):
    target: CompanyIdAndName
    investors: list[InvestorInRoundOfFunding]


class RoundOfFundingInfoTransaction(BaseModel):
    funding_type: str | None = None
    amount_offered: Decimal | None = None
    currency: str | None = None
    legal_fees: Decimal | None = None
    other_fees: Decimal | None = None
    initial_gross_amount_offered: Decimal | None = None
    offering_size_change: str | None = None
    upsized_amount: Decimal | None = None
    upsized_amount_percent: Decimal | None = None
    pre_money_valuation: Decimal | None = None
    post_money_valuation: Decimal | None = None
    aggregate_amount_raised: Decimal | None = None
    liquidation_preference: str | None = None
    anti_dilution_method: str | None = None
    option_pool: Decimal | None = None
    participating_preferred_cap: Decimal | None = None
    liquidation_preference_multiple: Decimal | None = None
    use_of_proceeds: str | None = None
    pre_deal_situation: str | None = None
    redemption: str | None = None
    cumulative_dividends: str | None = None
    reorganization: str | None = None
    pay_to_play: str | None = None
    pay_to_play_penalties: str | None = None


class RoundOfFundingInfoSecurity(BaseModel):
    dividend_per_share: Decimal | None = None
    annualized_dividend_rate: Decimal | None = None
    seniority_level: str | None = None
    coupon_type: str | None = None
    funding_convertible_type: str | None = None
    security_description: str | None = None
    class_series_tranche: str | None = None


class RoundOfFundingInfoTimeline(BaseModel):
    announced_date: date | None
    closed_date: date | None


class RoundOfFundingInfo(BaseModel):
    timeline: RoundOfFundingInfoTimeline
    participants: RoundOfFundingParticipants
    transaction: RoundOfFundingInfoTransaction
    security: RoundOfFundingInfoSecurity

    def with_advisors(
        self,
        target_advisors: list["AdvisorResp"] | None = None,
        investor_advisors: dict[int, list["AdvisorResp"]] | None = None,
    ) -> "RoundOfFundingInfoWithAdvisors":
        """Create a new RoundOfFundingInfoWithAdvisors by merging advisor data into this object.

        Args:
            target_advisors: List of advisors for the target company
            investor_advisors: Dict mapping investor company_id to their advisors list
        """
        # Create target with advisors
        target_with_advisors = CompanyIdAndNameWithAdvisors(
            company_id=self.participants.target.company_id,
            company_name=self.participants.target.company_name,
            advisors=target_advisors or [],
        )

        # Create investors with advisors
        investors_with_advisors = []
        for investor in self.participants.investors:
            investor_advisor_list = []
            if investor_advisors and investor.company_id in investor_advisors:
                investor_advisor_list = investor_advisors[investor.company_id]

            investor_with_advisors = InvestorInRoundOfFundingWithAdvisors(
                company_id=investor.company_id,
                company_name=investor.company_name,
                lead_investor=investor.lead_investor,
                investment_value=investor.investment_value,
                currency=investor.currency,
                advisors=investor_advisor_list,
            )
            investors_with_advisors.append(investor_with_advisors)

        return RoundOfFundingInfoWithAdvisors(
            timeline=self.timeline,
            participants=RoundOfFundingParticipantsWithAdvisors(
                target=target_with_advisors, investors=investors_with_advisors
            ),
            transaction=self.transaction,
            security=self.security,
        )


class FundingSummary(BaseModel):
    company_id: str
    total_capital_raised: float | None
    total_capital_raised_currency: str | None
    total_rounds: int
    first_funding_date: date | None
    most_recent_funding_date: date | None
    rounds_by_type: dict[str, int]  # {"Series A": 1, "Series B": 1, ...}
    sources: list[Source] = Field(default_factory=list)


class AdvisorResp(BaseModel):
    advisor_company_id: int
    advisor_company_name: str
    advisor_type_name: str | None
    advisor_fee_amount: float | None = None
    advisor_fee_currency: float | None = None
    is_lead: bool | None = None

    @field_serializer("advisor_company_id")
    def serialize_with_prefix(self, company_id: int) -> str:
        """Serialize the advisor_company_id with a prefix ("C_<company_id>").

        Including the prefix allows us to distinguish tickers and company_ids.
        """
        return f"{COMPANY_ID_PREFIX}{company_id}"


class AdvisorsResp(BaseModel):
    advisors: list[AdvisorResp]


class AdvisorTaskKey(BaseModel):
    """Key model for organizing advisor fetch tasks"""

    transaction_id: int
    role: AdvisedCompanyRole
    company_id: int

    def to_string(self) -> str:
        """Convert to string key for use in dictionaries"""
        return f"{self.role.value}_{self.transaction_id}_{self.company_id}"

    @classmethod
    def from_string(cls, key: str) -> "AdvisorTaskKey":
        """Parse string key back to AdvisorTaskKey"""
        parts = key.split("_", 2)
        if len(parts) != 3:
            raise ValueError(f"Invalid key format: {key}")
        role_str, transaction_id, company_id = parts
        return cls(
            transaction_id=int(transaction_id),
            role=AdvisedCompanyRole(role_str),
            company_id=int(company_id),
        )


class CompanyIdAndNameWithAdvisors(CompanyIdAndName):
    """A company with advisors information for funding rounds"""

    advisors: list[AdvisorResp] = Field(default_factory=list)


class InvestorInRoundOfFundingWithAdvisors(InvestorInRoundOfFunding):
    """An investor in a funding round with advisors information"""

    advisors: list[AdvisorResp] = Field(default_factory=list)


class RoundOfFundingParticipantsWithAdvisors(BaseModel):
    target: CompanyIdAndNameWithAdvisors
    investors: list[InvestorInRoundOfFundingWithAdvisors]


class RoundOfFundingInfoWithAdvisors(BaseModel):
    timeline: RoundOfFundingInfoTimeline
    participants: RoundOfFundingParticipantsWithAdvisors
    transaction: RoundOfFundingInfoTransaction
    security: RoundOfFundingInfoSecurity
