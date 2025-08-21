from datetime import date
from decimal import Decimal

from pydantic import BaseModel, field_serializer

from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX, CompanyIdAndName


class MergerSummary(BaseModel):
    transaction_id: int
    merger_title: str
    closed_date: date | None


class MergersResp(BaseModel):
    target: list[MergerSummary]
    buyer: list[MergerSummary]
    seller: list[MergerSummary]


class AdvisorResp(BaseModel):
    advisor_company_id: int
    advisor_company_name: str
    advisor_type_name: str | None

    @field_serializer("advisor_company_id")
    def serialize_with_prefix(self, company_id: int) -> str:
        """Serialize the advisor_company_id with a prefix ("C_<company_id>").

        Including the prefix allows us to distinguish tickers and company_ids.
        """
        return f"{COMPANY_ID_PREFIX}{company_id}"


class MergerTimelineElement(BaseModel):
    status: str
    date: date


class MergerParticipants(BaseModel):
    target: CompanyIdAndName
    buyers: list[CompanyIdAndName]
    sellers: list[CompanyIdAndName]


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
    details: list[MergerConsiderationDetail]


class MergerInfo(BaseModel):
    timeline: list[MergerTimelineElement]
    participants: MergerParticipants
    consideration: MergerConsideration
