from __future__ import annotations

from pydantic import BaseModel
from strenum import StrEnum


class TreeRelationshipType(StrEnum):
    """The type of parent-child relationship in the corporate tree: 'SUBSIDIARY_OR_OPERATING_UNIT', 'MERGED_ENTITY', 'INVESTMENT_ARM', 'AFFILIATE'."""

    subsidiary_or_operating_unit = "SUBSIDIARY_OR_OPERATING_UNIT"
    merged_entity = "MERGED_ENTITY"
    investment_arm = "INVESTMENT_ARM"
    affiliate = "AFFILIATE"


class TreeRelationshipStatus(StrEnum):
    """Whether the relationship is current or prior/historical: 'CURRENT', 'PRIOR'."""

    current = "CURRENT"
    prior = "PRIOR"


class CompanyInfo(BaseModel):
    """Basic company information within a corporate tree node."""

    id: int
    name: str
    country: str | None = None
    iso_country: str | None = None


class TreeNode(BaseModel):
    """A node in the corporate tree (recursive)."""

    company: CompanyInfo
    relationship_type: TreeRelationshipType
    relationship_status: TreeRelationshipStatus
    controlling_interest: bool
    children: list[TreeNode] = []


class RootNode(BaseModel):
    """The root node of the corporate tree."""

    company: CompanyInfo
    children: list[TreeNode] = []


class TruncationInfo(BaseModel):
    """Information about whether the tree was truncated due to size limits."""

    max_nodes: int
    returned_nodes: int
    max_level_reached: int


class CorporateTreeResponse(BaseModel):
    """The full API response for the corporate tree endpoint."""

    root: RootNode
    truncation: TruncationInfo | None = None
    ultimate_parent_path: list[CompanyInfo] | None = None
