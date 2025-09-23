"""Integration module for dynamic prompt construction with existing tool calling system."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from kfinance.client.permission_models import Permission

from .constructor import DynamicPromptConstructor
from .repository import ExampleRepository
from .search import SimilaritySearchEngine


logger = logging.getLogger(__name__)


class DynamicPromptManager:
    """Manager class for integrating dynamic prompt construction with the tool calling system."""

    def __init__(
        self,
        examples_dir: Optional[Path] = None,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        enable_caching: bool = True,
        cache_dir: Optional[Path] = None,
    ):
        """Initialize the dynamic prompt manager.

        Args:
            examples_dir: Directory containing example JSON files
            embedding_model: Name of the sentence transformer model
            enable_caching: Whether to enable embedding caching
            cache_dir: Directory to store embedding cache files
        """
        self.examples_dir = examples_dir
        self.embedding_model = embedding_model
        self.enable_caching = enable_caching
        self.cache_dir = cache_dir

        # Initialize components
        self._repository: Optional[ExampleRepository] = None
        self._similarity_engine: Optional[SimilaritySearchEngine] = None
        self._prompt_constructor: Optional[DynamicPromptConstructor] = None

        # Lazy initialization flag
        self._initialized = False

    def _initialize(self) -> None:
        """Lazy initialization of components."""
        if self._initialized:
            return

        try:
            # Initialize example repository
            self._repository = ExampleRepository(
                examples_dir=self.examples_dir,
                embedding_model=self.embedding_model,
                cache_embeddings=self.enable_caching,
                cache_dir=self.cache_dir,
            )

            # Initialize similarity search engine
            self._similarity_engine = SimilaritySearchEngine(
                embedding_model=self._repository.embedding_model,
            )

            # Initialize prompt constructor
            self._prompt_constructor = DynamicPromptConstructor(
                example_repository=self._repository,
                similarity_engine=self._similarity_engine,
            )

            self._initialized = True
            logger.info("Dynamic prompt manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize dynamic prompt manager: {e}")
            # Fall back to None components - will use static prompts
            self._repository = None
            self._similarity_engine = None
            self._prompt_constructor = None

    def construct_dynamic_prompt(
        self,
        query: str,
        user_permissions: Set[Permission],
        available_tools: Optional[List[str]] = None,
        min_similarity: float = 0.3,
    ) -> str:
        """Construct a dynamic prompt for the given query.

        Args:
            query: User query
            user_permissions: User's permissions
            available_tools: List of available tool names
            min_similarity: Minimum similarity threshold

        Returns:
            Dynamic prompt string, or base prompt if dynamic construction fails
        """
        self._initialize()

        if not self._prompt_constructor:
            # Fall back to base prompt if initialization failed
            from kfinance.integrations.tool_calling.prompts import BASE_PROMPT
            logger.warning("Dynamic prompt construction not available, using base prompt")
            return BASE_PROMPT

        try:
            return self._prompt_constructor.construct_prompt(
                query=query,
                user_permissions=user_permissions,
                available_tools=available_tools,
                min_similarity=min_similarity,
            )
        except Exception as e:
            logger.error(f"Failed to construct dynamic prompt: {e}")
            # Fall back to base prompt
            from kfinance.integrations.tool_calling.prompts import BASE_PROMPT
            return BASE_PROMPT

    def get_prompt_with_stats(
        self,
        query: str,
        user_permissions: Set[Permission],
        available_tools: Optional[List[str]] = None,
        min_similarity: float = 0.3,
    ) -> tuple[str, dict]:
        """Get dynamic prompt with statistics.

        Returns:
            Tuple of (prompt, statistics_dict)
        """
        self._initialize()

        if not self._prompt_constructor:
            from kfinance.integrations.tool_calling.prompts import BASE_PROMPT
            return BASE_PROMPT, {"error": "Dynamic prompt construction not available"}

        try:
            return self._prompt_constructor.construct_prompt_with_stats(
                query=query,
                user_permissions=user_permissions,
                available_tools=available_tools,
                min_similarity=min_similarity,
            )
        except Exception as e:
            logger.error(f"Failed to construct dynamic prompt with stats: {e}")
            from kfinance.integrations.tool_calling.prompts import BASE_PROMPT
            return BASE_PROMPT, {"error": str(e)}

    def search_similar_examples(
        self,
        query: str,
        user_permissions: Set[Permission],
        top_k: int = 5,
    ) -> List[dict]:
        """Search for similar examples (useful for debugging/analysis).

        Returns:
            List of example dictionaries with similarity scores
        """
        self._initialize()

        if not self._repository or not self._similarity_engine:
            return []

        try:
            similarity_results = self._similarity_engine.search_examples(
                query=query,
                examples=self._repository.examples,
                user_permissions=user_permissions,
                top_k=top_k,
            )

            # Convert to serializable format
            results = []
            for similarity, example in similarity_results:
                result = example.to_dict()
                result["similarity_score"] = float(similarity)
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Failed to search similar examples: {e}")
            return []

    def add_example_from_query(
        self,
        query: str,
        tool_name: str,
        parameters: dict,
        context: str,
        permissions_required: Set[Permission],
        disambiguation_note: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """Add a new example from a successful query (for continuous learning).

        Returns:
            True if example was added successfully, False otherwise
        """
        self._initialize()

        if not self._repository:
            return False

        try:
            from .models import ToolExample

            example = ToolExample(
                query=query,
                tool_name=tool_name,
                parameters=parameters,
                context=context,
                permissions_required=permissions_required,
                disambiguation_note=disambiguation_note,
                tags=tags or [],
            )

            self._repository.add_example(example)
            logger.info(f"Added new example for tool {tool_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add example: {e}")
            return False

    def get_repository_stats(self) -> Dict[str, Any]:
        """Get statistics about the example repository.

        Returns:
            Dictionary with repository statistics
        """
        self._initialize()

        if not self._repository:
            return {"error": "Repository not available"}

        try:
            stats: Dict[str, Any] = {
                "total_examples": len(self._repository.examples),
                "examples_by_tool": {},
                "total_parameter_descriptors": sum(
                    len(descriptors) for descriptors in self._repository.parameter_descriptors.values()
                ),
                "tools_with_descriptors": len(self._repository.parameter_descriptors),
            }

            # Count examples by tool
            for example in self._repository.examples:
                tool_name = example.tool_name
                if tool_name not in stats["examples_by_tool"]:
                    stats["examples_by_tool"][tool_name] = 0
                stats["examples_by_tool"][tool_name] += 1

            # Add cache statistics if available
            cache_stats = self._repository.get_cache_stats()
            if "error" not in cache_stats:
                stats["cache"] = cache_stats

            return stats

        except Exception as e:
            logger.error(f"Failed to get repository stats: {e}")
            return {"error": str(e)}

    def precompute_embeddings(self, force_recompute: bool = False) -> bool:
        """Precompute embeddings for all examples.

        Args:
            force_recompute: Whether to force recomputation of all embeddings

        Returns:
            True if successful, False otherwise
        """
        self._initialize()

        if not self._repository:
            return False

        try:
            self._repository.precompute_embeddings(force_recompute=force_recompute)
            logger.info("Successfully precomputed embeddings")
            return True
        except Exception as e:
            logger.error(f"Failed to precompute embeddings: {e}")
            return False

    def get_cache_stats(self) -> dict:
        """Get embedding cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        self._initialize()

        if not self._repository:
            return {"error": "Repository not available"}

        return self._repository.get_cache_stats()

    def invalidate_cache(self) -> bool:
        """Invalidate the embedding cache.

        Returns:
            True if successful, False otherwise
        """
        self._initialize()

        if not self._repository:
            return False

        try:
            self._repository.invalidate_cache()
            logger.info("Successfully invalidated cache")
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return False


# Global instance for easy access
_global_prompt_manager: Optional[DynamicPromptManager] = None


def get_dynamic_prompt_manager() -> DynamicPromptManager:
    """Get the global dynamic prompt manager instance."""
    global _global_prompt_manager

    if _global_prompt_manager is None:
        _global_prompt_manager = DynamicPromptManager()

    return _global_prompt_manager


def construct_dynamic_prompt(
    query: str,
    user_permissions: Set[Permission],
    available_tools: Optional[List[str]] = None,
) -> str:
    """Convenience function to construct a dynamic prompt.

    This is the main entry point for integrating with existing tool calling code.
    """
    manager = get_dynamic_prompt_manager()
    return manager.construct_dynamic_prompt(query, user_permissions, available_tools)
