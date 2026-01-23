from copy import deepcopy
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field
from strenum import StrEnum

from kfinance.client.models.response_models import Source
from kfinance.domains.companies.company_models import CompanyId, CompanyIdAndName


class RoundOfFunding(BaseModel):
    transaction_id: int
    funding_round_notes: str | None
    closed_date: date | None = None
    funding_type: str | None


class RoundsOfFundingResp(BaseModel):
    rounds_of_funding: list[RoundOfFunding]


class InvestorInRoundOfFunding(BaseModel):
    """An investor in a round of funding.

    Used in the results of fetch calls and merged with advisor data within the GetRoundsOfFundingInfoFromTransactionIds tool.
    """

    company_id: CompanyId
    company_name: str
    lead_investor: bool | None = None
    investment_value: Decimal | None = None
    currency: str | None = None
    ownership_percentage_pre: Decimal | None = None
    ownership_percentage_post: Decimal | None = None
    board_seat_granted: bool | None = None


class RoundsOfFundingRole(StrEnum):
    """The role of the company involved in the round of funding"""

    company_raising_funds = "company_raising_funds"
    company_investing_in_round_of_funding = "company_investing_in_round_of_funding"


class RoundOfFundingParticipants(BaseModel):
    """Round of funding participants.

    Used in the results of fetch calls and merged with advisor data within the GetRoundsOfFundingInfoFromTransactionIds tool.
    """

    target: CompanyIdAndName
    investors: list[InvestorInRoundOfFunding]


class RoundOfFundingInfoTransaction(BaseModel):
    """Transaction associated with a round of funding.

    The transaction describes the financial terms, valuation metrics, and rights structure
    established during the round of funding agreement.
    """

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
    """Security associated with a round of funding.

    The security is the asset that the investor(s) received and describes what the investor(s) owns after the deal closed.
    """

    dividend_per_share: Decimal | None = None
    annualized_dividend_rate: Decimal | None = None
    seniority_level: str | None = None
    coupon_type: str | None = None
    funding_convertible_type: str | None = None
    security_description: str | None = None
    class_series_tranche: str | None = None


class RoundOfFundingInfoTimeline(BaseModel):
    announced_date: date | None = None
    closed_date: date | None = None


class RoundOfFundingInfo(BaseModel):
    """Round of funding info.

    Used in the result of fetch calls and merged with advisor data within the GetRoundsOfFundingInfoFromTransactionIds tool.
    """

    timeline: RoundOfFundingInfoTimeline
    participants: RoundOfFundingParticipants
    transaction: RoundOfFundingInfoTransaction
    security: RoundOfFundingInfoSecurity

    def with_advisors(
        self,
        target_advisors: list["AdvisorResp"],
        investor_advisors: dict[int, list["AdvisorResp"]],
    ) -> "RoundOfFundingInfoWithAdvisors":
        """Create a new RoundOfFundingInfoWithAdvisors by merging advisor data into this object.

        Args:
            target_advisors: List of advisors for the target company
            investor_advisors: Dict mapping investor company_id to their advisors list
        """
        target_with_advisors = CompanyIdAndNameWithAdvisors(
            **self.participants.target.__dict__,
            advisors=target_advisors,
        )

        investors_with_advisors = []
        for investor in self.participants.investors:
            investor_advisor_list = investor_advisors.get(investor.company_id, [])

            investor_with_advisors = InvestorInRoundOfFundingWithAdvisors(
                **investor.__dict__,
                advisors=investor_advisor_list,
            )
            investors_with_advisors.append(investor_with_advisors)

        return RoundOfFundingInfoWithAdvisors(
            timeline=deepcopy(self.timeline),
            participants=RoundOfFundingParticipantsWithAdvisors(
                target=target_with_advisors, investors=investors_with_advisors
            ),
            transaction=deepcopy(self.transaction),
            security=deepcopy(self.security),
        )


class FundingSummary(BaseModel):
    """Funding summary included derived fields.

    total_rounds, first_funding_date, most_recent_funding_date, and rounds_by_type are derived from underlying rounds of funding data that might be non-comprehensive.
    """

    company_id: str
    total_capital_raised: float | None
    total_capital_raised_currency: str | None
    total_rounds: int
    first_funding_date: date | None
    most_recent_funding_date: date | None
    rounds_by_type: dict[str, int]  # {"Series A": 1, "Series B": 1, ...}
    sources: list[Source] = Field(default_factory=list)


class AdvisorResp(BaseModel):
    """Advisor for a participant (either target or investor) in a round of funding.

    Used in tool response.
    """

    advisor_company_id: CompanyId
    advisor_company_name: str
    advisor_type_name: str | None
    advisor_fee_amount: float | None = None
    advisor_fee_currency: str | None = None
    is_lead: bool | None = None


class AdvisorsResp(BaseModel):
    """List of advisors for a participant (either target or investor) in a round of funding.

    Used in tool response.
    """

    advisors: list[AdvisorResp]


class AdvisorTaskKey(BaseModel):
    """Key model for organizing advisor fetch tasks"""

    transaction_id: int
    role: RoundsOfFundingRole
    company_id: int

    def to_string(self) -> str:
        """Convert to string key for use in dictionaries"""
        # Map the role to shorter strings for key generation
        role_short = (
            "target" if self.role == RoundsOfFundingRole.company_raising_funds else "investor"
        )
        return f"{role_short}_{self.transaction_id}_{self.company_id}"

    @classmethod
    def from_string(cls, key: str) -> "AdvisorTaskKey":
        """Parse string key back to AdvisorTaskKey"""
        parts = key.split("_", 2)
        if len(parts) != 3:
            raise ValueError(f"Invalid key format: {key}")
        role_str, transaction_id, company_id = parts
        # Map short strings back to enum values
        role = (
            RoundsOfFundingRole.company_raising_funds
            if role_str == "target"
            else RoundsOfFundingRole.company_investing_in_round_of_funding
        )
        return cls(
            transaction_id=int(transaction_id),
            role=role,
            company_id=int(company_id),
        )


class CompanyIdAndNameWithAdvisors(CompanyIdAndName):
    """A company with advisors information for rounds of funding.

    Used in tool response.
    """

    advisors: list[AdvisorResp] = Field(default_factory=list)


class InvestorInRoundOfFundingWithAdvisors(InvestorInRoundOfFunding):
    """An investor in a round of funding with advisors information.

    Used in tool response.
    """

    advisors: list[AdvisorResp] = Field(default_factory=list)


class RoundOfFundingParticipantsWithAdvisors(BaseModel):
    """Round of funding participants with advisors.

    Used in tool response.
    """

    target: CompanyIdAndNameWithAdvisors
    investors: list[InvestorInRoundOfFundingWithAdvisors]


class RoundOfFundingInfoWithAdvisors(BaseModel):
    """Round of funding info including advisors for participants.

    Used in tool response.
    """

    timeline: RoundOfFundingInfoTimeline
    participants: RoundOfFundingParticipantsWithAdvisors
    transaction: RoundOfFundingInfoTransaction
    security: RoundOfFundingInfoSecurity
