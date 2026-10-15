from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from kfinance.client.models.response_models import RespWithErrors
from kfinance.domains.companies.company_models import CompanyId


class OwnerPosition(BaseModel):
    """An owner's position in a company.

    Attributes:
        shares_held: Shares of the company held by the owner at the end of the period.
        percent_shares_outstanding: Percent of the company's total shares outstanding held by the owner.
        shares_changed: Shares bought (positive) or sold (negative) by the owner during the period.
        percent_shares_changed: shares_changed as a percent of the owner's prior period position.
        holding_date: The observation date for the position.
    """

    shares_held: int
    percent_shares_outstanding: Decimal | None = None
    shares_changed: int
    percent_shares_changed: Decimal | None = None
    holding_date: datetime


class Owner(BaseModel):
    """An owner of a company.

    Attributes:
        owner_id: The id of the company or person that owns the company.
        owner_name: The name of the company or person that owns the company.
        institution_type: The type of institution the owner is (e.g. "Investment Adviser").
        position: The owner's latest position in the company.
    """

    owner_id: int
    owner_name: str | None = None
    institution_type: str | None = None
    position: OwnerPosition


class Owners(BaseModel):
    """The owners of a company, ordered by shares held, largest first."""

    ownership: list[Owner] = Field(default_factory=list)


class OwnersResp(RespWithErrors):
    """The API response for the owners endpoint."""

    results: Owners = Field(default_factory=Owners)


class OwnerTypeSummary(BaseModel):
    """Shares of a company held by one owner type (e.g. "Institutions", "Individuals/Insiders")."""

    owner_type: str
    shares_held: int


class OwnersSummary(BaseModel):
    """Latest-period institutional ownership summary for a company.

    Attributes:
        institutional_shares_held: Total shares held by all institutional holders.
        number_of_holders: Number of distinct institutional holders.
        shares_bought: Total shares bought by institutions during the period.
        shares_sold: Total shares sold by institutions during the period.
        number_of_buyers: Number of institutions that bought shares during the period.
        number_of_sellers: Number of institutions that sold shares during the period.
        number_of_new_buyers: Number of institutions that opened a new position during the period.
        number_of_closed_positions: Number of institutions that fully exited their position.
        institutional_ownership_pct: Percent of the company's total shares outstanding held by institutions.
        by_owner_type: Shares held broken down by owner type, ordered by shares held, largest first.
    """

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
    """The API response for the owners summary endpoint."""

    results: OwnersSummary | None = None


class CompanyOwners(BaseModel):
    """The owners of a company, optionally with the company's ownership summary.

    The per-identifier result of the get_owners_from_identifiers tool, which combines the owners
    and owners summary endpoints.
    """

    summary: OwnersSummary | None = None
    owners: list[Owner] = Field(default_factory=list)


class HoldingPosition(BaseModel):
    """An owner's position in a single security.

    Attributes:
        security_id: The id of the security held by the owner.
        ticker: The ticker of the security held by the owner.
        shares_held: Shares of the security held by the owner at the end of the period.
        percent_of_portfolio: Percent of the owner's portfolio represented by the position.
        percent_shares_outstanding: Percent of the held company's total shares outstanding held by the owner.
        holding_date: The observation date for the position.
    """

    security_id: int
    ticker: str | None = None
    shares_held: int
    percent_of_portfolio: Decimal | None = None
    percent_shares_outstanding: Decimal | None = None
    holding_date: datetime


class Holding(BaseModel):
    """A company held by an owner, with the owner's positions in that company's securities.

    Positions are ordered by shares held, largest first.
    """

    held_company_id: CompanyId | None = None
    held_company_name: str | None = None
    positions: list[HoldingPosition]


class Holdings(BaseModel):
    """The holdings of an owner, ordered by largest position, largest first."""

    holdings: list[Holding] = Field(default_factory=list)


class HoldingsResp(RespWithErrors):
    """The API response for the holdings endpoint."""

    results: Holdings = Field(default_factory=Holdings)


class InsiderTrade(BaseModel):
    """A single insider trade.

    Attributes:
        owner_id: The id of the person or company that made the trade.
        insider_name: The person's full name, or the company's name.
        transaction_type: The type of transaction (e.g. "Open Market Acquisition", "Sale").
        security_type: The security traded (e.g. "Common Stock").
        shares: Shares traded, negative for dispositions.
        min_price: Minimum transaction price per share.
        max_price: Maximum transaction price per share.
        transaction_value_usd: Total transaction value in USD.
        trade_date: The date of the trade.
        filing_date: The date the trade was filed with the SEC.
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


class InsiderTrades(BaseModel):
    """The insider trades of a company, ordered most recent first."""

    trades: list[InsiderTrade] = Field(default_factory=list)


class InsiderTradesResp(RespWithErrors):
    """The API response for the insider trades endpoint."""

    results: InsiderTrades = Field(default_factory=InsiderTrades)
