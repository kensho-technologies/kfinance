from datetime import date

from pydantic import BaseModel


class MergerSummary(BaseModel):
    transaction_id: int
    merger_title: str
    closed_date: date


class MergersResp(BaseModel):
    target: list[MergerSummary]
    buyer: list[MergerSummary]
    seller: list[MergerSummary]
