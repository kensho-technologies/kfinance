from pydantic import BaseModel, Field
from strenum import StrEnum

from kfinance.domains.companies.company_models import CompanyId


class CompanyType(StrEnum):
    """What kind of entity a company in the corporate tree is.

    This spans every type the API can return, including entities that are not companies in
    the ordinary sense, such as indexes, funds, commodities and rate or yield curve profiles.
    Those show up as children in a tree but cannot themselves be used as a tree root.
    """

    public_investment_firm = "public_investment_firm"
    private_investment_firm = "private_investment_firm"
    assets_products = "assets_products"
    public_company = "public_company"
    private_company = "private_company"
    corporate_investment_arm = "corporate_investment_arm"
    financial_service_investment_arm = "financial_service_investment_arm"
    index = "index"  # type: ignore[assignment]  # shadows str.index, which is never used here
    private_fund = "private_fund"
    fund_family = "fund_family"
    currency_rate = "currency_rate"
    public_fund = "public_fund"
    interest_rate = "interest_rate"
    educational_institution = "educational_institution"
    arts_institution = "arts_institution"
    labor_union = "labor_union"
    government_institution = "government_institution"
    religious_institution = "religious_institution"
    trade_association = "trade_association"
    foundation_charitable_institution = "foundation_charitable_institution"
    industry = "industry"
    commodity = "commodity"
    rate_group = "rate_group"
    yield_curve = "yield_curve"
    gcp_industry = "gcp_industry"
    corporate_yield_curve_all_tenor_profile = "corporate_yield_curve_all_tenor_profile"
    corporate_yield_curve_tenor_profile = "corporate_yield_curve_tenor_profile"


class TreeRelationshipType(StrEnum):
    """The type of parent-child relationship in the corporate tree.

    Every relationship in the corporate tree is a controlling one. Minority and other
    non-controlling stakes are absent from the tree and from the ultimate parent paths.
    """

    subsidiary_or_operating_unit = "subsidiary_or_operating_unit"
    merged_entity = "merged_entity"
    investment_arm = "investment_arm"
    affiliated_government_institution = "affiliated_government_institution"


class TreeRelationshipStatus(StrEnum):
    """Whether the relationship is current or prior/historical."""

    current = "current"
    prior = "prior"


class CompanyInfo(BaseModel):
    """Basic identifying information for a company in the corporate tree."""

    company_id: CompanyId
    company_name: str
    company_type: CompanyType | None = None
    country: str | None = None
    iso_country: str | None = None


class CorporateTreeNode(BaseModel):
    """One parent-child relationship in the flat corporate tree list."""

    company: CompanyInfo
    parent_company_id: CompanyId
    level: int
    relationship_type: TreeRelationshipType
    relationship_status: TreeRelationshipStatus


class TreeSummary(BaseModel):
    """Aggregate statistics about the corporate tree."""

    total_companies: int
    total_edges: int
    max_depth: int


class TruncationInfo(BaseModel):
    """Companies at the depth limit whose children were not included in the tree.

    Present only when max_depth was supplied and the tree continues past it.
    """

    truncated_company_ids: list[CompanyId]


class CorporateTreeResponse(BaseModel):
    """The full API response for the corporate tree endpoint."""

    root: CompanyInfo
    nodes: list[CorporateTreeNode]
    summary: TreeSummary
    truncation: TruncationInfo | None = None


class ParentPathElement(BaseModel):
    """An element in the path from a company up to one of its ultimate parents.

    `relationship_type` describes the edge up to this element's own parent, so the ultimate
    parent at the end of a path has neither a `parent_company_id` nor a `relationship_type`.
    """

    company_id: CompanyId
    company_name: str
    company_type: CompanyType | None = None
    country: str | None = None
    iso_country: str | None = None
    parent_company_id: CompanyId | None = None
    relationship_type: TreeRelationshipType | None = None


class UltimateParentPathsResponse(BaseModel):
    """The full API response for the ultimate parent paths endpoint.

    Every path starts at the requested company and ends with the ultimate parent of that path.
    A company with no controlling parent yields a single path holding only that company.
    """

    paths: list[list[ParentPathElement]]


class SearchMatch(BaseModel):
    """A single matching relationship returned from a corporate tree search."""

    company_id: CompanyId
    company_name: str
    company_type: CompanyType | None = None
    country: str | None = None
    iso_country: str | None = None
    parent_company_id: CompanyId
    level: int
    relationship_type: TreeRelationshipType
    relationship_status: TreeRelationshipStatus


class SearchSummary(BaseModel):
    """Summary metadata about the search results and the portion of the tree they were drawn from.

    Derived client-side from the matches and the tree's own summary.
    """

    total_matches: int = Field(
        description="Matching relationships. A company owned through several parents matches once per parent."
    )
    distinct_companies: int = Field(description="Distinct companies among the matches.")
    showing: int = Field(
        description="Matches included in `matches`, capped by the `limit` argument. When it is below total_matches, narrow the filters to see the rest; there is no way to page through results."
    )
    matches_by_level: dict[str, int] = Field(
        description="Count of matches at each level below the queried company, where level 1 is a direct child."
    )
    companies_searched: int = Field(
        description="Distinct companies searched, counting the queried company. Capped by max_depth, so this is NOT the size of the full tree unless the whole tree was searched."
    )
    relationships_searched: int = Field(
        description="Parent-child relationships searched. Larger than companies_searched when companies have several parents. Also capped by max_depth."
    )
    deepest_level_searched: int = Field(
        description="The deepest level actually reached. When the search was depth-limited this is just max_depth."
    )
    search_was_depth_limited: bool = Field(
        description="True when max_depth stopped the search before the tree ended, meaning the counts above describe only the searched portion."
    )


class CorporateTreeSearchResult(BaseModel):
    """Search results from a company's corporate tree."""

    queried_company: CompanyInfo
    matches: list[SearchMatch]
    summary: SearchSummary
