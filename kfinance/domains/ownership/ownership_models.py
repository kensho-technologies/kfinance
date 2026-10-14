from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from kfinance.client.models.response_models import RespWithErrors
from kfinance.domains.companies.company_models import CompanyId


class OwnerPosition(BaseModel):
    """An owner's position in a company.

    percent_shares_changed is None when there's no prior period to compute a change against.
    """

    shares_held: int
    percent_shares_outstanding: Decimal | None = None
    shares_changed: int
    percent_shares_changed: Decimal | None = None
    holding_date: datetime


class Owner(BaseModel):
    """An institutional owner of a company.

    owner_id can be either a company id or a person id.
    """

    owner_id: int
    owner_name: str | None = None
    institution_type: str | None = None
    position: OwnerPosition


class OwnersResult(BaseModel):
    ownership: list[Owner] = Field(default_factory=list)


class OwnersResp(RespWithErrors):
    results: OwnersResult = Field(default_factory=OwnersResult)


class OwnerTypeSummary(BaseModel):
    """Shares of a company held by one owner type (e.g. "Institutions", "Individuals/Insiders")."""

    owner_type: str
    shares_held: int


class OwnersSummary(BaseModel):
    """Latest-period institutional ownership summary for a company."""

    institutional_shares_held: int
    number_of_holders: int
    shares_bought: int
    shares_sold: int
    number_of_buyers: int
    number_of_sellers: int
    number_of_new_buyers: int
    number_of_closed_positions: int
    institutional_ownership_pct: Decimal | None = None
    by_owner_type: list[OwnerTypeSummary] = Field(default_factory=list)


class OwnersSummaryResp(RespWithErrors):
    results: OwnersSummary | None = None


class CompanyOwners(BaseModel):
    """The owners of a company, optionally with the company's ownership summary."""

    summary: OwnersSummary | None = None
    owners: list[Owner] = Field(default_factory=list)


class HoldingPosition(BaseModel):
    """An owner's position in a single security."""

    security_id: int
    ticker: str | None = None
    shares_held: int
    percent_of_portfolio: Decimal | None = None
    percent_shares_outstanding: Decimal | None = None
    holding_date: datetime


class Holding(BaseModel):
    """A company held by an owner, with the owner's positions in that company's securities.

    held_company_id is None when the security isn't mapped to a company (e.g. ETFs or indices).
    """

    held_company_id: CompanyId | None = None
    held_company_name: str | None = None
    positions: list[HoldingPosition]


class HoldingsResult(BaseModel):
    holdings: list[Holding] = Field(default_factory=list)


class HoldingsResp(RespWithErrors):
    results: HoldingsResult = Field(default_factory=HoldingsResult)


class InsiderTrade(BaseModel):
    """A single insider trade.

    shares is negative for dispositions. When a record covers trades over several days,
    trade_date is the latest date.
    """

    owner_id: int
    insider_name: str | None = None
    transaction_type: str | None = None
    security_type: str | None = None
    shares: Decimal | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    transaction_value_usd: Decimal | None = None
    trade_date: datetime | None = None
    filing_date: datetime | None = None


class InsiderTradesResult(BaseModel):
    trades: list[InsiderTrade] = Field(default_factory=list)


class InsiderTradesResp(RespWithErrors):
    results: InsiderTradesResult = Field(default_factory=InsiderTradesResult)
