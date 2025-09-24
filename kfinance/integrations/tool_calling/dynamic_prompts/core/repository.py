"""Example repository for storing and managing tool usage examples and parameter descriptors."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from kfinance.client.permission_models import Permission

from ..processing.entities import EntityProcessor
from .cache import EmbeddingCache
from .models import ParameterDescriptor, ToolExample


logger = logging.getLogger(__name__)


class ExampleRepository:
    """Repository for managing tool usage examples and parameter descriptors."""

    def __init__(
        self,
        examples_dir: Optional[Path] = None,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        cache_embeddings: bool = True,
        cache_dir: Optional[Path] = None,
    ):
        """Initialize the example repository.

        Args:
            examples_dir: Directory containing example JSON files
            embedding_model: Name of the sentence transformer model to use
            cache_embeddings: Whether to cache computed embeddings
            cache_dir: Directory to store embedding cache files
        """
        self.examples_dir = examples_dir or self._get_default_examples_dir()
        self.embedding_model_name = embedding_model
        self.cache_embeddings = cache_embeddings

        # Initialize embedding cache
        self.embedding_cache = (
            EmbeddingCache(
                cache_dir=cache_dir,
                embedding_model_name=embedding_model,
            )
            if cache_embeddings
            else None
        )

        # Get embedding model from cache (lazy loaded)
        self.embedding_model = (
            self.embedding_cache.embedding_model if self.embedding_cache else None
        )

        # Entity processing
        self.entity_processor = EntityProcessor()

        # Storage
        self.examples: List[ToolExample] = []
        self.parameter_descriptors: Dict[str, List[ParameterDescriptor]] = {}

        # Load examples and descriptors
        self._load_examples()
        self._load_parameter_descriptors()

        # Load or compute embeddings
        if self.embedding_cache and self.examples:
            self._load_or_compute_embeddings()

    def _get_default_examples_dir(self) -> Path:
        """Get the default examples directory."""
        # Go up one level from core/ to the main dynamic_prompts directory
        current_dir = Path(__file__).parent.parent
        return current_dir / "tool_examples"

    def _load_examples(self) -> None:
        """Load tool usage examples from JSON files."""
        if not self.examples_dir.exists():
            logger.warning("Examples directory not found: %s", self.examples_dir)
            return

        for json_file in self.examples_dir.glob("*_examples.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)

                total_examples_loaded = 0

                # Handle both old format (examples at top level) and new format (tools with examples)
                if "examples" in data:
                    # Old format: {"examples": [...]}
                    for example_data in data["examples"]:
                        example = ToolExample.from_dict(example_data)
                        self.examples.append(example)
                        total_examples_loaded += 1
                elif "tools" in data:
                    # New format: {"tools": [{"tool_name": "...", "examples": [...]}]}
                    for tool_data in data["tools"]:
                        for example_data in tool_data.get("examples", []):
                            example = ToolExample.from_dict(example_data)
                            self.examples.append(example)
                            total_examples_loaded += 1

                logger.debug("Loaded %d examples from %s", total_examples_loaded, json_file.name)

            except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error("Failed to load examples from %s: %s", json_file, e)

    def _load_parameter_descriptors(self) -> None:
        """Load parameter descriptors from JSON files."""
        descriptors_dir = self.examples_dir.parent / "parameter_descriptors"

        if not descriptors_dir.exists():
            logger.warning("Parameter descriptors directory not found: %s", descriptors_dir)
            return

        for json_file in descriptors_dir.glob("*_params.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)

                # Handle both old format (tool_name at top level) and new format (tools array)
                if "tool_name" in data:
                    # Old format: {"tool_name": "...", "parameters": [...]}
                    tool_name = data.get("tool_name")
                    if tool_name:
                        descriptors = []
                        for param_data in data.get("parameters", []):
                            descriptor = ParameterDescriptor.from_dict(param_data)
                            descriptors.append(descriptor)
                        self.parameter_descriptors[tool_name] = descriptors
                        logger.debug("Loaded %d parameter descriptors for %s", len(descriptors), tool_name)
                
                elif "tools" in data:
                    # New format: {"tools": [{"tool_name": "...", "parameters": [...]}]}
                    for tool_data in data["tools"]:
                        tool_name = tool_data.get("tool_name")
                        if not tool_name:
                            continue
                        
                        descriptors = []
                        for param_data in tool_data.get("parameters", []):
                            descriptor = ParameterDescriptor.from_dict(param_data)
                            descriptors.append(descriptor)
                        
                        self.parameter_descriptors[tool_name] = descriptors
                        logger.debug("Loaded %d parameter descriptors for %s", len(descriptors), tool_name)

            except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error("Failed to load parameter descriptors from %s: %s", json_file, e)

    def _load_or_compute_embeddings(self) -> None:
        """Load cached embeddings or compute new ones as needed."""
        if not self.embedding_cache:
            return

        try:
            # Use embedding cache to get or compute embeddings
            self.examples = self.embedding_cache.get_or_compute_embeddings(self.examples)

            # Clean up orphaned embeddings
            self.embedding_cache.cleanup_orphaned_embeddings(self.examples)

            logger.debug("Loaded/computed embeddings for %d examples", len(self.examples))

        except (RuntimeError, ValueError, OSError) as e:
            logger.error("Failed to load/compute embeddings: %s", e)

    def normalize_query_for_search(self, query: str) -> Tuple[str, Dict[str, str]]:
        """Normalize a query for semantic search by replacing entities with placeholders.

        Args:
            query: Original user query

        Returns:
            Tuple of (normalized_query, entity_mapping)
        """
        return self.entity_processor.process_query(query)

    def search_examples(
        self,
        query: str,
        user_permissions: Set[Permission],
        tool_names: Optional[List[str]] = None,
        top_k: int = 5,
        min_similarity: float = 0.3,
    ) -> List[ToolExample]:
        """Search for relevant examples using cosine similarity.

        Args:
            query: User query to search for
            user_permissions: User's permissions for filtering
            tool_names: Optional list of tool names to filter by
            top_k: Maximum number of examples to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of relevant tool examples, sorted by similarity
        """
        if not self.embedding_model or not self.examples:
            return []

        # Normalize query to reduce entity bias
        normalized_query, entity_mapping = self.normalize_query_for_search(query)

        # Filter examples by permissions and tool names
        filtered_examples = []
        for example in self.examples:
            # Check permissions - user needs at least one of the required permissions
            if not example.permissions_required.intersection(user_permissions):
                continue

            # Check tool names if specified
            if tool_names and example.tool_name not in tool_names:
                continue

            filtered_examples.append(example)

        if not filtered_examples:
            return []

        # Compute query embedding using normalized query
        try:
            query_embedding = self.embedding_model.encode([normalized_query])[0]
        except (RuntimeError, ValueError, OSError) as e:
            logger.error("Failed to compute query embedding: %s", e)
            return []

        # Calculate similarities
        similarities = []
        for example in filtered_examples:
            if example.embedding is not None:
                similarity = np.dot(query_embedding, example.embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(example.embedding)
                )
                if similarity >= min_similarity:
                    similarities.append((similarity, example))

        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [example for _, example in similarities[:top_k]]

    def get_parameter_descriptors(self, tool_name: str) -> List[ParameterDescriptor]:
        """Get parameter descriptors for a specific tool."""
        return self.parameter_descriptors.get(tool_name, [])

    def add_example(self, example: ToolExample) -> None:
        """Add a new example to the repository."""
        # Add to examples list first
        self.examples.append(example)

        # Compute embedding using cache if available
        if self.embedding_cache:
            try:
                # Get embedding for the new example
                examples_with_embeddings = self.embedding_cache.get_or_compute_embeddings([example])
                if examples_with_embeddings and examples_with_embeddings[0].embedding is not None:
                    example.embedding = examples_with_embeddings[0].embedding
            except (RuntimeError, ValueError, OSError) as e:
                logger.error("Failed to compute embedding for new example: %s", e)
        elif self.embedding_model:
            # Fallback to direct computation if no cache
            try:
                embedding = self.embedding_model.encode([example.query])[0]
                example.embedding = embedding
            except (RuntimeError, ValueError, OSError) as e:
                logger.error("Failed to compute embedding for new example (fallback): %s", e)

    def save_examples(self, output_file: Path) -> None:
        """Save examples to a JSON file."""
        data = {"examples": [example.to_dict() for example in self.examples]}

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info("Saved %d examples to %s", len(self.examples), output_file)

    def precompute_embeddings(self, force_recompute: bool = False) -> None:
        """Precompute embeddings for all examples.

        Args:
            force_recompute: Whether to force recomputation of all embeddings
        """
        if not self.embedding_cache:
            logger.warning("No embedding cache available for precomputation")
            return

        self.examples = self.embedding_cache.get_or_compute_embeddings(
            self.examples, force_recompute=force_recompute
        )
        logger.info("Precomputed embeddings for %d examples", len(self.examples))

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get embedding cache statistics."""
        if not self.embedding_cache:
            return {"error": "No embedding cache available"}

        return self.embedding_cache.get_cache_stats()

    def invalidate_cache(self) -> None:
        """Invalidate the embedding cache."""
        if self.embedding_cache:
            self.embedding_cache.invalidate_cache()
            # Clear embeddings from examples
            for example in self.examples:
                example.embedding = None
            logger.info("Invalidated embedding cache")
        else:
            logger.warning("No embedding cache to invalidate")
