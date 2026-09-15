from pydantic import BaseModel, Field
from strenum import StrEnum

from kfinance.domains.companies.company_models import CompanyId


class TreeRelationshipType(StrEnum):
    """The type of parent-child relationship in the corporate tree."""

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
