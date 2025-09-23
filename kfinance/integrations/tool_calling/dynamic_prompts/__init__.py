"""Dynamic prompt construction system for kfinance tool calling."""

from typing import Set

from kfinance.client.permission_models import Permission

from .core.cache import EmbeddingCache
from .core.constructor import DynamicPromptConstructor
from .core.manager import DynamicPromptManager
from .core.models import ParameterDescriptor, ToolExample
from .core.repository import ExampleRepository
from .core.search import SimilaritySearchEngine
from .processing.entities import EntityProcessor


def construct_dynamic_prompt(
    query: str,
    user_permissions: Set[Permission],
    enable_caching: bool = True
) -> str:
    """Convenience function to construct a dynamic prompt for a given query.

    Args:
        query: The user query to construct a prompt for
        user_permissions: Set of permissions the user has
        enable_caching: Whether to enable embedding caching

    Returns:
        Dynamically constructed prompt string
    """
    manager = DynamicPromptManager(enable_caching=enable_caching)
    return manager.construct_dynamic_prompt(query, user_permissions)


__all__ = [
    "DynamicPromptManager",
    "ToolExample",
    "ParameterDescriptor",
    "ExampleRepository",
    "SimilaritySearchEngine",
    "DynamicPromptConstructor",
    "EmbeddingCache",
    "EntityProcessor",
    "construct_dynamic_prompt",
]
