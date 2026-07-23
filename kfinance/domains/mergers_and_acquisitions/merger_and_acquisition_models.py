from datetime import date as date_type
from decimal import Decimal

from pydantic import BaseModel

from kfinance.domains.companies.company_models import CompanyId, CompanyIdAndName


class MergerSummary(BaseModel):
    transaction_id: int
    status: str
    start_date: date_type | None
    closed_date: date_type | None
    target: str
    buyers: list[str]


class MergersResp(BaseModel):
    target: list[MergerSummary]
    buyer: list[MergerSummary]
    seller: list[MergerSummary]


class AdvisorResp(BaseModel):
    advisor_company_id: CompanyId
    advisor_company_name: str
    advisor_type_name: str | None
    advisor_fee_amount: Decimal | None
    advisor_fee_currency: str | None


class MergerTimelineElement(BaseModel):
    status: str
    date: date_type


class MergerParticipant(CompanyIdAndName):
    percent_ownership: Decimal | None
    advisors: list[AdvisorResp] | None


class MergerDetails(BaseModel):
    buy_side_termination_fee: Decimal | None
    sell_side_termination_fee: Decimal | None
    comment: str | None


class MergerParticipants(BaseModel):
    target: MergerParticipant
    buyers: list[MergerParticipant]
    sellers: list[MergerParticipant]


class MergerConsiderationDetail(BaseModel):
    scenario: str | None = None
    subtype: str | None = None
    cash_or_cash_equivalent_per_target_share_unit: Decimal | None = None
    number_of_target_shares_sought: Decimal | None = None
    current_calculated_gross_value_of_consideration: Decimal | None = None


class MergerConsideration(BaseModel):
    currency_name: str | None = None
    current_calculated_gross_total_transaction_value: Decimal | None = None
    current_calculated_implied_equity_value: Decimal | None = None
    current_calculated_implied_enterprise_value: Decimal | None = None
    presentation_gross_total_transaction_value: Decimal | None = None
    presentation_implied_equity_value: Decimal | None = None
    presentation_implied_enterprise_value: Decimal | None = None
    target_stock_premium_1_day_prior: Decimal | None = None
    target_stock_premium_7_days_prior: Decimal | None = None
    target_stock_premium_30_days_prior: Decimal | None = None
    current_calculated_tev_ebit: Decimal | None = None
    current_calculated_tev_ebitda: Decimal | None = None
    current_calculated_tev_revenues: Decimal | None = None
    current_calculated_equity_net_income: Decimal | None = None
    presentation_tev_ebit: Decimal | None = None
    presentation_tev_ebitda: Decimal | None = None
    presentation_tev_revenues: Decimal | None = None
    presentation_equity_net_income: Decimal | None = None
    details: list[MergerConsiderationDetail]


class MergerInfo(BaseModel):
    timeline: list[MergerTimelineElement]
    participants: MergerParticipants
    consideration: MergerConsideration | None = None
    details: MergerDetails | None


class NoMergerFound(BaseModel):
    error: str


class MergersInfo(BaseModel):
    results: dict[int, MergerInfo | NoMergerFound]
