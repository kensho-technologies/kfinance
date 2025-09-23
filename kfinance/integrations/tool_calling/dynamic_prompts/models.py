"""Data models for dynamic prompt construction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import numpy as np

from kfinance.client.permission_models import Permission
from .permission_resolver import get_permission_resolver


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
        """Create ToolExample from dictionary."""
        permission_refs = data.get("permissions_required", [])
        resolver = get_permission_resolver()
        permissions = resolver.resolve_permissions(permission_refs)
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
