from pydantic import BaseModel
from strenum import StrEnum


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

    company_id: int
    company_name: str
    country: str | None = None
    iso_country: str | None = None


class CorporateTreeNode(BaseModel):
    """One parent-child relationship in the flat corporate tree list.

    The tree is returned as an edge list rather than a nested structure. Parentage is expressed
    solely by `parent_company_id`, which points at either the root company or the company of
    another node.

    `level` is the shallowest depth at which the relationship was found, so it is NOT always
    `parent.level + 1`. Rebuild the graph by following `parent_company_id`, never by doing
    arithmetic on `level`.
    """

    company: CompanyInfo
    parent_company_id: int
    level: int
    relationship_type: TreeRelationshipType
    relationship_status: TreeRelationshipStatus


class TreeSummary(BaseModel):
    """Aggregate statistics about the corporate tree, computed server-side."""

    # Distinct companies in the tree, counting the root.
    total_companies: int
    # Parent-child relationships in the tree, i.e. len(nodes). The root has no incoming edge, so
    # a tree with no relationships has total_companies=1 and total_edges=0. A company with
    # multiple parents makes total_companies smaller than total_edges.
    total_edges: int
    max_depth: int


class TruncationInfo(BaseModel):
    """Companies at the depth limit whose children were not included in the tree.

    Present only when max_depth was supplied and the tree continues past it.
    """

    truncated_company_ids: list[int]


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

    company_id: int
    company_name: str
    country: str | None = None
    iso_country: str | None = None
    parent_company_id: int | None = None
    relationship_type: TreeRelationshipType | None = None


class UltimateParentPathsResponse(BaseModel):
    """The full API response for the ultimate parent paths endpoint.

    Every path starts at the requested company and ends with the ultimate parent of that path.
    A company with no controlling parent yields a single path holding only that company.
    """

    paths: list[list[ParentPathElement]]
