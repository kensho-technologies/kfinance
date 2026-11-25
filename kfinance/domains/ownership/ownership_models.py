from datetime import date, datetime
from typing import NamedTuple

from pydantic import BaseModel, Field
from strenum import StrEnum

from kfinance.client.models.response_models import RespWithErrors
from kfinance.domains.companies.company_models import CompanyId
from kfinance.domains.corporate_tree.corporate_tree_models import CompanyType


# Owner, holding and transaction types are kept as plain strings in the API response models, so
# that a type the server adds later doesn't break parsing. The enums below are only used to build
# requests.


class ApiOwnerType(StrEnum):
    """The owner types accepted by the owners API's owner_types filter."""

    institution = "institution"
    public_corporation = "public_corporation"
    private_corporation = "private_corporation"
    individual_insider = "individual_insider"
    company_controlled_foundation = "company_controlled_foundation"
    esop = "esop"
    state_owned = "state_owned"
    strategic_hedge_fund_manager = "strategic_hedge_fund_manager"
    strategic_vc_pe_firm = "strategic_vc_pe_firm"
    strategic_sovereign_wealth_fund = "strategic_sovereign_wealth_fund"


class OwnerTypeCategory(StrEnum):
    """The owner types exposed by the owners tool, each grouping one or more API owner types."""

    all = "all"
    institutions = "institutions"
    individuals = "individuals"
    corporations = "corporations"
    other = "other"


# The API owner types of each category. `all` sends no filter.
OWNER_TYPES_BY_CATEGORY: dict[OwnerTypeCategory, list[ApiOwnerType]] = {
    # Hedge fund managers, VC/PE firms and sovereign wealth funds are "institution" below a 5%
    # stake in a company and strategic_* above it, so both belong with institutions.
    OwnerTypeCategory.institutions: [
        ApiOwnerType.institution,
        ApiOwnerType.strategic_hedge_fund_manager,
        ApiOwnerType.strategic_vc_pe_firm,
        ApiOwnerType.strategic_sovereign_wealth_fund,
    ],
    OwnerTypeCategory.individuals: [ApiOwnerType.individual_insider],
    OwnerTypeCategory.corporations: [
        ApiOwnerType.public_corporation,
        ApiOwnerType.private_corporation,
    ],
    OwnerTypeCategory.other: [
        ApiOwnerType.company_controlled_foundation,
        ApiOwnerType.esop,
        ApiOwnerType.state_owned,
    ],
}


class PositionChange(StrEnum):
    """The change in an owner's position since the previous reporting period.

    - bought: The owner increased its position (shares_changed > 0).
    - sold: The owner decreased its position (shares_changed < 0).
    - new: The owner newly appears in the data (percent_shares_changed is null).
    - closed: The owner fully exited its position (shares_held = 0).
    """

    bought = "bought"
    sold = "sold"
    new = "new"
    closed = "closed"


class FundsView(StrEnum):
    """Which owners to return, by whether they're a fund with an active fund parent."""

    exclude_funds = "exclude_funds"
    include_funds = "include_funds"
    funds_only = "funds_only"


class OwnersSortBy(StrEnum):
    """How to order a company's owners. Every order is descending."""

    shares_held = "shares_held"
    absolute_shares_changed = "absolute_shares_changed"


class HeldCompanyTypeCategory(StrEnum):
    """The held company types exposed by the holdings tool, each grouping one or more CompanyTypes."""

    all = "all"
    public_companies = "public_companies"
    private_companies = "private_companies"
    funds = "funds"
    investment_firms = "investment_firms"
    other = "other"


_GROUPED_HELD_COMPANY_TYPES: dict[HeldCompanyTypeCategory, list[CompanyType]] = {
    HeldCompanyTypeCategory.public_companies: [CompanyType.public_company],
    HeldCompanyTypeCategory.private_companies: [CompanyType.private_company],
    HeldCompanyTypeCategory.funds: [
        CompanyType.public_fund,
        CompanyType.private_fund,
        CompanyType.fund_family,
    ],
    HeldCompanyTypeCategory.investment_firms: [
        CompanyType.public_investment_firm,
        CompanyType.private_investment_firm,
        CompanyType.corporate_investment_arm,
        CompanyType.financial_service_investment_arm,
    ],
}

# The company types of each category. `all` sends no filter, and `other` is every type that isn't
# in another category.
HELD_COMPANY_TYPES_BY_CATEGORY: dict[HeldCompanyTypeCategory, list[CompanyType]] = {
    **_GROUPED_HELD_COMPANY_TYPES,
    HeldCompanyTypeCategory.other: [
        company_type
        for company_type in CompanyType
        if not any(company_type in types for types in _GROUPED_HELD_COMPANY_TYPES.values())
    ],
}


class ApiInsiderTransactionType(StrEnum):
    """The transaction types accepted by the insider trades API's transaction_types filter."""

    initial_statement_of_beneficial_ownership_form_3 = (
        "initial_statement_of_beneficial_ownership_form_3"
    )
    derivative_exercise_and_retained_stock = "derivative_exercise_and_retained_stock"
    derivative_exercise_and_sale = "derivative_exercise_and_sale"
    open_market_acquisition = "open_market_acquisition"
    open_market_derivative_acquisition = "open_market_derivative_acquisition"
    open_market_disposition = "open_market_disposition"
    open_market_derivative_disposition = "open_market_derivative_disposition"
    private_acquisition = "private_acquisition"
    private_disposition = "private_disposition"
    acquisition_under_employee_benefit_plan = "acquisition_under_employee_benefit_plan"
    derivative_acquisition_under_employee_benefit_plan = (
        "derivative_acquisition_under_employee_benefit_plan"
    )
    disposition_under_employee_benefit_plan = "disposition_under_employee_benefit_plan"
    derivative_disposition_under_employee_benefit_plan = (
        "derivative_disposition_under_employee_benefit_plan"
    )
    automatic_acquisition = "automatic_acquisition"
    automatic_disposition = "automatic_disposition"
    sale_to_issuer = "sale_to_issuer"
    derivative_sale_to_issuer = "derivative_sale_to_issuer"
    other_acquisition = "other_acquisition"
    other_derivative_acquisition = "other_derivative_acquisition"
    other_disposition = "other_disposition"
    other_derivative_disposition = "other_derivative_disposition"
    derivative_exercise = "derivative_exercise"
    sale = "sale"
    intent_to_sell_form_144 = "intent_to_sell_form_144"


class InsiderActivityType(StrEnum):
    """A group of insider activity. Every API transaction type is in exactly one group.

    - open_market: Open market purchases and sales, including of derivatives.
    - automatic: Automatic transactions under a trading plan (e.g. Rule 10b5-1).
    - derivatives: Option grants and exercises, and other derivative transactions that aren't on
      the open market.
    - other: The other transactions: awards and employee benefit plan transactions, private
      transactions, gifts, sales to the issuer (mostly tax withholding) and other sales.
    - disclosures: Filings that aren't transactions: Form 144 notices of a planned sale, and
      Form 3 initial statements of holdings.
    """

    open_market = "open_market"
    automatic = "automatic"
    derivatives = "derivatives"
    other = "other"
    disclosures = "disclosures"


# The groups returned when no activity_types are given: every transaction, but no disclosures.
DEFAULT_INSIDER_ACTIVITY_TYPES: list[InsiderActivityType] = [
    InsiderActivityType.open_market,
    InsiderActivityType.automatic,
    InsiderActivityType.derivatives,
    InsiderActivityType.other,
]


class TransactionDirection(StrEnum):
    """Whether to return acquisitions, dispositions, or both."""

    acquisitions = "acquisitions"
    dispositions = "dispositions"
    both = "both"


class InsiderTransactionTypeAttributes(NamedTuple):
    """How an API insider transaction type is selected by the insider activity tool.

    Attributes:
        group: The activity group the type is in.
        direction: Whether it's an acquisition or a disposition, or None for neither.
    """

    group: InsiderActivityType
    direction: TransactionDirection | None


_OPEN_MARKET, _AUTOMATIC, _DERIVATIVES, _OTHER, _DISCLOSURES = (
    InsiderActivityType.open_market,
    InsiderActivityType.automatic,
    InsiderActivityType.derivatives,
    InsiderActivityType.other,
    InsiderActivityType.disclosures,
)
_ACQ, _DISP = TransactionDirection.acquisitions, TransactionDirection.dispositions
_A = InsiderTransactionTypeAttributes
_T = ApiInsiderTransactionType

INSIDER_TRANSACTION_TYPE_ATTRIBUTES: dict[
    ApiInsiderTransactionType, InsiderTransactionTypeAttributes
] = {
    _T.open_market_acquisition: _A(_OPEN_MARKET, _ACQ),
    _T.open_market_disposition: _A(_OPEN_MARKET, _DISP),
    # Open market trades in derivatives are rare, so they stay with the other open market trades.
    _T.open_market_derivative_acquisition: _A(_OPEN_MARKET, _ACQ),
    _T.open_market_derivative_disposition: _A(_OPEN_MARKET, _DISP),
    _T.automatic_acquisition: _A(_AUTOMATIC, _ACQ),
    _T.automatic_disposition: _A(_AUTOMATIC, _DISP),
    _T.derivative_acquisition_under_employee_benefit_plan: _A(_DERIVATIVES, _ACQ),
    _T.derivative_disposition_under_employee_benefit_plan: _A(_DERIVATIVES, _DISP),
    _T.other_derivative_acquisition: _A(_DERIVATIVES, _ACQ),
    _T.other_derivative_disposition: _A(_DERIVATIVES, _DISP),
    _T.derivative_sale_to_issuer: _A(_DERIVATIVES, _DISP),
    # Exercising an option acquires the underlying shares; with a same-day sale of the shares, the
    # net effect is a disposition.
    _T.derivative_exercise: _A(_DERIVATIVES, _ACQ),
    _T.derivative_exercise_and_retained_stock: _A(_DERIVATIVES, _ACQ),
    _T.derivative_exercise_and_sale: _A(_DERIVATIVES, _DISP),
    _T.acquisition_under_employee_benefit_plan: _A(_OTHER, _ACQ),
    _T.disposition_under_employee_benefit_plan: _A(_OTHER, _DISP),
    _T.private_acquisition: _A(_OTHER, _ACQ),
    _T.private_disposition: _A(_OTHER, _DISP),
    _T.other_acquisition: _A(_OTHER, _ACQ),
    _T.other_disposition: _A(_OTHER, _DISP),
    _T.sale_to_issuer: _A(_OTHER, _DISP),
    _T.sale: _A(_OTHER, _DISP),
    # A Form 144 notice announces a planned sale; a Form 3 states initial holdings, with no direction.
    _T.intent_to_sell_form_144: _A(_DISCLOSURES, _DISP),
    _T.initial_statement_of_beneficial_ownership_form_3: _A(_DISCLOSURES, None),
}


def select_insider_transaction_types(
    activity_types: list[InsiderActivityType] | None,
    direction: TransactionDirection,
) -> list[ApiInsiderTransactionType]:
    """Return the API transaction types in the activity groups, in the direction.

    No activity_types means every transaction group, without disclosures. A direction other than
    both drops types with no direction.
    """
    groups = set(activity_types or DEFAULT_INSIDER_ACTIVITY_TYPES)
    return [
        transaction_type
        for transaction_type, attributes in INSIDER_TRANSACTION_TYPE_ATTRIBUTES.items()
        if attributes.group in groups
        and (direction == TransactionDirection.both or attributes.direction == direction)
    ]


class InsiderTradesSortBy(StrEnum):
    """How to order insider trades. Every order is descending."""

    date = "date"
    absolute_transaction_value_usd = "absolute_transaction_value_usd"
    absolute_shares = "absolute_shares"


class ReportingPeriod(BaseModel):
    """An ownership reporting period, generally three months."""

    start_date: date
    end_date: date


class PeriodChange(BaseModel):
    """The change in an owner's position from the previous reporting period.

    Attributes:
        shares_changed: Shares bought (positive) or sold (negative) during the period. Equals
            shares_held when there's no prior period.
        percent_shares_changed: shares_changed as a percent of the prior period's position. Null
            when the owner newly appears in the data.
    """

    shares_changed: int
    percent_shares_changed: float | None = None


class FundParent(BaseModel):
    """The active sponsor or investment advisor of a fund.

    Attributes:
        company_id: The fund parent's company id.
        company_name: The fund parent's name.
        is_owner: Whether the fund parent is also an owner of the company.
    """

    company_id: CompanyId
    company_name: str | None = None
    is_owner: bool


class Owner(BaseModel):
    """An owner of a company, from the Ownership dataset.

    Attributes:
        owner_id: The id of the company or person that owns the company.
        owner_name: The name of the company or person that owns the company.
        owner_type: The type of the owner's holding in the company (e.g. "institution").
        institution_type: The type of institution the owner is.
        shares_held: Shares of the company held at the end of the period.
        percent_shares_outstanding: Percent of the company's shares outstanding held.
        holding_date: The observation date for the holding.
        reporting_period: The reporting period the position is recorded for.
        period_change: The change in the position from the previous reporting period.
        fund_parent: The fund's sponsor or investment advisor, when the owner is a fund.
    """

    owner_id: int
    owner_name: str | None = None
    owner_type: str | None = None
    institution_type: str | None = None
    shares_held: int
    percent_shares_outstanding: float | None = None
    holding_date: date
    reporting_period: ReportingPeriod | None = None
    period_change: PeriodChange
    fund_parent: FundParent | None = None


class OwnerTypeCoverage(BaseModel):
    """The part of a company's shares held by owners of one type."""

    owner_type: str | None = None
    owners: int
    pct_shares_outstanding: float | None = None


class FundsCoverage(BaseModel):
    """The part of a company's shares held by funds with an active fund parent."""

    owners: int
    pct_shares_outstanding: float | None = None


class OwnersCoverage(BaseModel):
    """How much of a company's shares outstanding the Ownership dataset's owners account for."""

    total_owners: int
    total_pct_shares_outstanding: float | None = None
    by_owner_type: list[OwnerTypeCoverage] = Field(default_factory=list)
    funds: FundsCoverage | None = None


class OwnersResult(BaseModel):
    owners: list[Owner] = Field(default_factory=list)
    total_matching: int = 0
    coverage: OwnersCoverage | None = None


class OwnersResp(RespWithErrors):
    """The API response for the owners endpoint."""

    results: OwnersResult = Field(default_factory=OwnersResult)


class OwnerTypeSummary(BaseModel):
    """Shares of a company held by one owner type.

    Attributes:
        owner_type: An owner type as returned on each owner (e.g. "institution",
            "individual_insider"), or "public_and_other" for the shares not held by an identified
            owner. Null when the source data has an owner type the API doesn't know.
        shares_held: Total shares held by this owner type. Can be negative for a small number of
            companies in the source data.
    """

    owner_type: str | None = None
    shares_held: int


# The API's summary owner type for the shares not held by an identified owner (CIQ's "Public and
# Other"). No single owner has it.
API_PUBLIC_AND_OTHER = "public_and_other"
# What the tool calls those shares, so they aren't confused with the owner_type category "other".
UNATTRIBUTED = "unattributed"

_CATEGORY_BY_API_OWNER_TYPE: dict[str, OwnerTypeCategory] = {
    str(api_type): category
    for category, api_types in OWNER_TYPES_BY_CATEGORY.items()
    for api_type in api_types
}


def sum_by_owner_type_category(by_owner_type: list[OwnerTypeSummary]) -> list[OwnerTypeSummary]:
    """Sum the summary's shares held into the owner_type categories of the owners tool.

    The summary reports the API's owner types (e.g. institution, strategic_vc_pe_firm), while the
    tool filters on broader categories (e.g. institutions), so this makes both use one vocabulary.
    The shares not held by an identified owner (the API's public_and_other) are kept as their own
    entry, unattributed. Owner types the client doesn't know, including null, count as other.
    Entries are ordered by shares held, largest first.
    """
    totals: dict[str, int] = {}
    for entry in by_owner_type:
        if entry.owner_type == API_PUBLIC_AND_OTHER:
            key = UNATTRIBUTED
        else:
            key = str(
                _CATEGORY_BY_API_OWNER_TYPE.get(entry.owner_type or "", OwnerTypeCategory.other)
            )
        totals[key] = totals.get(key, 0) + entry.shares_held
    return sorted(
        (OwnerTypeSummary(owner_type=key, shares_held=shares) for key, shares in totals.items()),
        key=lambda entry: (-entry.shares_held, entry.owner_type or ""),
    )


class OwnersSummary(BaseModel):
    """The latest-period institutional ownership summary of a company.

    Attributes:
        institutional_shares_held: Total shares held by all institutional holders.
        number_of_holders: Number of distinct institutional holders.
        shares_bought: Total shares bought by institutions during the period.
        shares_sold: Total shares sold by institutions during the period.
        number_of_buyers: Number of institutions that bought shares during the period.
        number_of_sellers: Number of institutions that sold shares during the period.
        number_of_new_buyers: Number of institutions that opened a new position during the period.
        number_of_closed_positions: Number of institutions that fully exited their position.
        institutional_ownership_pct: Percent of the company's shares outstanding held by institutions.
        reporting_period: The reporting period the stats are recorded for.
        by_owner_type: Shares held broken down by owner type, largest first.
    """

    institutional_shares_held: int
    number_of_holders: int
    shares_bought: int
    shares_sold: int
    number_of_buyers: int
    number_of_sellers: int
    number_of_new_buyers: int
    number_of_closed_positions: int
    institutional_ownership_pct: float | None = None
    reporting_period: ReportingPeriod | None = None
    by_owner_type: list[OwnerTypeSummary] = Field(default_factory=list)


class OwnersSummaryResp(RespWithErrors):
    """The API response for the owners summary endpoint."""

    results: OwnersSummary | None = None


class CompanyOwners(BaseModel):
    """The per-identifier result of the get_owners_from_identifiers tool.

    Attributes:
        summary: The company's ownership summary, when requested. Its by_owner_type is summed into
            the tool's owner_type categories, plus unattributed.
        owners: The owners matching the filters, up to the limit.
        total_matching: The number of owners matching the filters, before the limit.
    """

    summary: OwnersSummary | None = None
    owners: list[Owner] = Field(default_factory=list)
    total_matching: int | None = None


class HoldingPosition(BaseModel):
    """An owner's position in a single security.

    Attributes:
        security_id: The id of the security held.
        ticker: The ticker of the security held.
        shares_held: Shares of the security held at the end of the period.
        percent_of_portfolio: Percent of the owner's portfolio represented by the position.
        percent_shares_outstanding: Percent of the held company's shares outstanding held.
        holding_date: The observation date for the position.
    """

    security_id: int
    ticker: str | None = None
    shares_held: int
    percent_of_portfolio: float | None = None
    percent_shares_outstanding: float | None = None
    holding_date: date


class Holding(BaseModel):
    """A company held by an owner, from the Ownership dataset.

    Attributes:
        held_company_id: The id of the held company. Null for securities not mapped to a company.
        held_company_name: The name of the held company.
        held_company_type: The held company's type (e.g. "public_company").
        total_percent_of_portfolio: The sum of percent_of_portfolio over the positions.
        positions: The owner's positions in the held company's securities.
    """

    held_company_id: CompanyId | None = None
    held_company_name: str | None = None
    held_company_type: str | None = None
    total_percent_of_portfolio: float | None = None
    positions: list[HoldingPosition] = Field(default_factory=list)


class HeldCompanyTypeCoverage(BaseModel):
    """The part of an owner's portfolio held in companies of one type."""

    company_type: str | None = None
    held_companies: int
    pct_portfolio: float | None = None


class HoldingsCoverage(BaseModel):
    """How much of an owner's full, unfiltered portfolio the Ownership dataset covers."""

    total_held_companies: int
    total_pct_portfolio: float | None = None
    by_held_company_type: list[HeldCompanyTypeCoverage] = Field(default_factory=list)


class HoldingsResult(BaseModel):
    holdings: list[Holding] = Field(default_factory=list)
    total_matching: int = 0
    coverage: HoldingsCoverage | None = None


class HoldingsResp(RespWithErrors):
    """The API response for the holdings endpoint."""

    results: HoldingsResult = Field(default_factory=HoldingsResult)


class OwnerHoldings(BaseModel):
    """The per-identifier result of the get_holdings_from_identifiers tool.

    Attributes:
        holdings: The holdings matching the filters, up to the limit.
        total_matching: The number of holdings matching the filters, before the limit.
    """

    holdings: list[Holding] = Field(default_factory=list)
    total_matching: int


class InsiderTrade(BaseModel):
    """A single insider trade.

    Attributes:
        owner_id: The id of the person or company that made the trade.
        insider_name: The person's full name, or the company's name.
        transaction_type: The type of transaction (e.g. "open_market_acquisition", "sale").
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
    shares: float | None = None
    min_price: float | None = None
    max_price: float | None = None
    transaction_value_usd: float | None = None
    trade_date: date | None = None
    filing_date: datetime | None = None


class InsiderTradesResult(BaseModel):
    trades: list[InsiderTrade] = Field(default_factory=list)
    total_matching: int = 0


class InsiderTradesResp(RespWithErrors):
    """The API response for the insider trades endpoint."""

    results: InsiderTradesResult = Field(default_factory=InsiderTradesResult)


class CompanyInsiderActivity(BaseModel):
    """The per-identifier result of the get_insider_activity_from_identifiers tool.

    Attributes:
        activity: The insider transactions or disclosures matching the filters, up to the limit.
        total_matching: The number of records matching the filters, before the limit.
    """

    activity: list[InsiderTrade] = Field(default_factory=list)
    total_matching: int
