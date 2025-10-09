from datetime import date
from decimal import Decimal
from strenum import StrEnum

from pydantic import BaseModel, field_serializer

from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX, CompanyIdAndName

class RoundOfFunding(BaseModel):
    transaction_id: int
    funding_round_notes: str
    closed_date: date | None

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

    @field_serializer("company_id")
    def serialize_with_prefix(self, company_id: int) -> str:
        """Serialize the investor company_id with a prefix ("C_<company_id>").

        Including the prefix allows us to distinguish tickers and company_ids.
        """
        return f"{COMPANY_ID_PREFIX}{company_id}"



class RoundsofFundingRole(StrEnum):
    """The role of the company involved in the round of funding"""
    company_raising_funds = "company_raising_funds"
    company_investing_in_round_of_funding = "company_investing_in_round_of_funding"

class RoundOfFundingParticipants(BaseModel):
    target: CompanyIdAndName 
    investors: list[InvestorInRoundOfFunding]

class RoundOfFundingInfoTransaction(BaseModel):
    funding_type: str | None = None
    amount_offered: Decimal | None = None
    currency_name: str | None = None
    legal_fees: Decimal | None = None
    other_fees: Decimal | None = None
    initial_gross_amount_offered: Decimal | None = None
    offering_size_change: str | None = None
    upsized_amount: Decimal | None = None
    upsized_amount_percent: Decimal | None = None
    pre_money_valuation: Decimal | None = None
    post_money_valuation: Decimal | None = None
    aggregate_amount_raised:Decimal | None = None
    liquidation_preference:str | None = None
    anti_dilution_method: str | None = None
    option_pool: Decimal | None = None
    participating_preferred_cap: Decimal | None = None
    liquidation_preference_multiple: Decimal | None = None
    use_of_proceeds:str | None = None
    pre_deal_situation: str | None = None
    redemption: str | None = None
    cumulative_dividends: str | None = None
    reorganization: str | None = None
    pay_to_play:str | None = None
    pay_to_play_penalties: str | None = None

class RoundOfFundingInfoSecurity(BaseModel):
    dividend_per_share:Decimal | None = None
    annualized_dividend_rate:Decimal | None = None
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

