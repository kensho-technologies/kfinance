"""Similarity search engine for finding relevant tool examples."""

from __future__ import annotations

import logging
from typing import List, Optional, Set, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

from kfinance.client.permission_models import Permission

from .models import ToolExample


logger = logging.getLogger(__name__)


class SimilaritySearchEngine:
    """Engine for performing similarity-based search on tool examples."""

    def __init__(
        self,
        embedding_model: Optional[SentenceTransformer] = None,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        """Initialize the similarity search engine.

        Args:
            embedding_model: Pre-initialized embedding model
            embedding_model_name: Name of the model to load if embedding_model is None
        """
        if embedding_model:
            self.embedding_model = embedding_model
        else:
            try:
                self.embedding_model = SentenceTransformer(embedding_model_name)
            except (OSError, ImportError, RuntimeError) as e:
                logger.error("Failed to load embedding model %s: %s", embedding_model_name, e)
                self.embedding_model = None

    def compute_similarity(
        self, query_embedding: np.ndarray, example_embedding: np.ndarray
    ) -> float:
        """Compute cosine similarity between two embeddings.

        Args:
            query_embedding: Query embedding vector
            example_embedding: Example embedding vector

        Returns:
            Cosine similarity score between 0 and 1
        """
        try:
            similarity = np.dot(query_embedding, example_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(example_embedding)
            )
            # Ensure similarity is between 0 and 1
            return max(0.0, min(1.0, similarity))
        except (ValueError, ZeroDivisionError, RuntimeError) as e:
            logger.error("Failed to compute similarity: %s", e)
            return 0.0

    def search_examples(
        self,
        query: str,
        examples: List[ToolExample],
        user_permissions: Set[Permission],
        tool_names: Optional[List[str]] = None,
        top_k: int = 5,
        min_similarity: float = 0.3,
        boost_exact_matches: bool = True,
    ) -> List[Tuple[float, ToolExample]]:
        """Search for relevant examples using cosine similarity.

        Args:
            query: User query to search for
            examples: List of tool examples to search through
            user_permissions: User's permissions for filtering
            tool_names: Optional list of tool names to filter by
            top_k: Maximum number of examples to return
            min_similarity: Minimum similarity threshold
            boost_exact_matches: Whether to boost examples with exact keyword matches

        Returns:
            List of (similarity_score, example) tuples, sorted by similarity
        """
        if not self.embedding_model:
            logger.warning("No embedding model available for similarity search")
            return []

        # Filter examples by permissions and tool names
        filtered_examples = self._filter_examples(examples, user_permissions, tool_names)

        if not filtered_examples:
            return []

        # Compute query embedding
        try:
            query_embedding = self.embedding_model.encode([query])[0]
        except (RuntimeError, ValueError, OSError) as e:
            logger.error("Failed to compute query embedding: %s", e)
            return []

        # Calculate similarities
        similarities = []
        query_lower = query.lower()

        for example in filtered_examples:
            if example.embedding is None:
                continue

            # Compute base similarity
            similarity = self.compute_similarity(query_embedding, example.embedding)

            # Apply boosting for exact matches if enabled
            if boost_exact_matches:
                similarity = self._apply_similarity_boosting(similarity, query_lower, example)

            if similarity >= min_similarity:
                similarities.append((similarity, example))

        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[0], reverse=True)
        return similarities[:top_k]

    def _filter_examples(
        self,
        examples: List[ToolExample],
        user_permissions: Set[Permission],
        tool_names: Optional[List[str]] = None,
    ) -> List[ToolExample]:
        """Filter examples by permissions and tool names."""
        filtered_examples = []

        for example in examples:
            # Check permissions
            if not example.permissions_required.issubset(user_permissions):
                continue

            # Check tool names if specified
            if tool_names and example.tool_name not in tool_names:
                continue

            filtered_examples.append(example)

        return filtered_examples

    def _apply_similarity_boosting(
        self,
        base_similarity: float,
        query_lower: str,
        example: ToolExample,
    ) -> float:
        """Apply boosting to similarity score based on exact matches and other factors.

        Args:
            base_similarity: Base cosine similarity score
            query_lower: Lowercase query string
            example: Tool example to check for matches

        Returns:
            Boosted similarity score
        """
        boost_factor = 1.0

        # Boost for exact keyword matches in query
        example_query_lower = example.query.lower()
        query_words = set(query_lower.split())
        example_words = set(example_query_lower.split())

        # Calculate word overlap
        word_overlap = len(query_words.intersection(example_words))
        if word_overlap > 0:
            overlap_ratio = word_overlap / len(query_words)
            boost_factor += overlap_ratio * 0.2  # Up to 20% boost for word overlap

        # Boost for parameter name matches
        for param_name, param_value in example.parameters.items():
            if isinstance(param_value, str) and param_value.lower() in query_lower:
                boost_factor += 0.1  # 10% boost for parameter matches

        # Boost for tag matches
        for tag in example.tags:
            if tag.lower() in query_lower:
                boost_factor += 0.05  # 5% boost per tag match

        # Apply boost but cap at reasonable maximum
        boosted_similarity = base_similarity * boost_factor
        return min(boosted_similarity, 1.0)

    def find_similar_parameters(
        self,
        parameter_name: str,
        tool_name: str,
        examples: List[ToolExample],
        threshold: float = 0.7,
    ) -> List[Tuple[str, float]]:
        """Find parameters similar to the given parameter name.

        This is useful for parameter disambiguation and suggesting alternatives.

        Args:
            parameter_name: Name of the parameter to find similar ones for
            tool_name: Name of the tool
            examples: List of examples to search through
            threshold: Similarity threshold for matches

        Returns:
            List of (parameter_name, similarity) tuples
        """
        if not self.embedding_model:
            return []

        try:
            param_embedding = self.embedding_model.encode([parameter_name])[0]
        except (RuntimeError, ValueError, OSError) as e:
            logger.error("Failed to compute parameter embedding: %s", e)
            return []

        similar_params = []
        seen_params = set()

        for example in examples:
            if example.tool_name != tool_name:
                continue

            for param_name, param_value in example.parameters.items():
                if param_name in seen_params:
                    continue

                seen_params.add(param_name)

                try:
                    param_name_embedding = self.embedding_model.encode([param_name])[0]
                    similarity = self.compute_similarity(param_embedding, param_name_embedding)

                    if similarity >= threshold and param_name != parameter_name:
                        similar_params.append((param_name, similarity))

                except (RuntimeError, ValueError, ZeroDivisionError) as e:
                    logger.error("Failed to compute similarity for parameter %s: %s", param_name, e)
                    continue

        # Sort by similarity
        similar_params.sort(key=lambda x: x[1], reverse=True)
        return similar_params

    def encode_text(self, text: str) -> Optional[np.ndarray]:
        """Encode text into embedding vector.

        Args:
            text: Text to encode

        Returns:
            Embedding vector or None if encoding fails
        """
        if not self.embedding_model:
            return None

        try:
            return self.embedding_model.encode([text])[0]
        except (RuntimeError, ValueError, OSError) as e:
            logger.error("Failed to encode text: %s", e)
            return None
