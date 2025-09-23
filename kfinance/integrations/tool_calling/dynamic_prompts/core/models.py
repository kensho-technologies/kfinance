"""Data models for dynamic prompt construction with integrated permission resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional, Set

import numpy as np


logger = logging.getLogger(__name__)

# Import Permission model with fallback for development
try:
    from kfinance.client.permission_models import Permission
except ImportError:
    logger.warning("Could not import Permission model - using mock for development")
    from enum import Enum

    class Permission(Enum):  # type: ignore[no-redef]
        StatementsPermission = "StatementsPermission"
        PricingPermission = "PricingPermission"
        EarningsPermission = "EarningsPermission"
        MergersPermission = "MergersPermission"
        CompanyIntelligencePermission = "CompanyIntelligencePermission"
        RelationshipPermission = "RelationshipPermission"
        SegmentsPermission = "SegmentsPermission"
        IDPermission = "IDPermission"
        CompetitorsPermission = "CompetitorsPermission"
        TranscriptsPermission = "TranscriptsPermission"


# Permission mapping for resolving references
PERMISSION_MAPPING = {
    # Financial data permissions
    "STATEMENTS": Permission.StatementsPermission,
    "PRICING": Permission.PricingPermission,
    "EARNINGS": Permission.EarningsPermission,

    # Company data permissions
    "COMPANY_INTELLIGENCE": Permission.CompanyIntelligencePermission,
    "MERGERS": Permission.MergersPermission,
    "RELATIONSHIPS": Permission.RelationshipPermission,
    "SEGMENTS": Permission.SegmentsPermission,
    "COMPETITORS": Permission.CompetitorsPermission,

    # Identifier and utility permissions
    "ID": Permission.IDPermission,
    "TRANSCRIPTS": Permission.TranscriptsPermission,

    # Handle both singular and plural forms
    "RELATIONSHIP": Permission.RelationshipPermission,
}


def resolve_permissions(permission_refs: List[str]) -> Set[Permission]:
    """Resolve permission reference strings to Permission enum values.

    Args:
        permission_refs: List of permission reference strings (e.g., ["STATEMENTS", "PRICING"])

    Returns:
        Set of Permission enum values
    """
    resolved_permissions = set()

    for ref in permission_refs:
        if ref in PERMISSION_MAPPING:
            resolved_permissions.add(PERMISSION_MAPPING[ref])
        else:
            # Try to resolve as direct Permission enum value
            try:
                resolved_permissions.add(Permission(ref))
            except (ValueError, AttributeError):
                logger.warning(f"Could not resolve permission reference: {ref}")

    return resolved_permissions


@dataclass
class ToolExample:
    """Represents a single tool usage example with context and embeddings."""

    query: str
    tool_name: str
    parameters: Dict[str, Any]
    context: str
    permissions_required: Set[Permission]
    embedding: Optional[np.ndarray] = field(default=None, repr=False)
    disambiguation_note: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization (excluding embedding)."""
        return {
            "query": self.query,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "context": self.context,
            "permissions_required": [p.value for p in self.permissions_required],
            "disambiguation_note": self.disambiguation_note,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolExample":
        """Create ToolExample from dictionary with integrated permission resolution."""
        permission_refs = data.get("permissions_required", [])
        permissions = resolve_permissions(permission_refs)
        return cls(
            query=data["query"],
            tool_name=data["tool_name"],
            parameters=data["parameters"],
            context=data["context"],
            permissions_required=permissions,
            disambiguation_note=data.get("disambiguation_note"),
            tags=data.get("tags", []),
        )


@dataclass
class ParameterDescriptor:
    """Enhanced parameter description for disambiguation."""

    parameter_name: str
    tool_name: str
    description: str
    examples: List[str]
    common_mistakes: List[str] = field(default_factory=list)
    related_parameters: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "parameter_name": self.parameter_name,
            "tool_name": self.tool_name,
            "description": self.description,
            "examples": self.examples,
            "common_mistakes": self.common_mistakes,
            "related_parameters": self.related_parameters,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParameterDescriptor":
        """Create ParameterDescriptor from dictionary."""
        return cls(
            parameter_name=data["parameter_name"],
            tool_name=data["tool_name"],
            description=data["description"],
            examples=data["examples"],
            common_mistakes=data.get("common_mistakes", []),
            related_parameters=data.get("related_parameters", []),
        )
