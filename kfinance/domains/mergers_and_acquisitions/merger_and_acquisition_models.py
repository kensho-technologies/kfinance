from datetime import date

from pydantic import BaseModel


class MergerSummary(BaseModel):
    transaction_id: int
    merger_title: str
    closed_date: date | None


class MergersResp(BaseModel):
    target: list[MergerSummary]
    buyer: list[MergerSummary]
    seller: list[MergerSummary]


class AdvisorResp(BaseModel):
    advisor_company_id: str
    advisor_company_name: str
    advisor_type_name: str | None
