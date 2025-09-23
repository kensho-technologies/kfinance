"""Embedding cache system for pre-computed example embeddings."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
import pickle
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from .models import ToolExample


logger = logging.getLogger(__name__)


class EmbeddingCache:
    """Cache system for pre-computed embeddings with automatic invalidation."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        """Initialize the embedding cache.

        Args:
            cache_dir: Directory to store cache files
            embedding_model_name: Name of the embedding model
        """
        self.cache_dir = cache_dir or self._get_default_cache_dir()
        self.embedding_model_name = embedding_model_name
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache file paths
        self.embeddings_cache_file = self.cache_dir / "embeddings.pkl"
        self.metadata_cache_file = self.cache_dir / "metadata.json"

        # Initialize embedding model lazily
        self._embedding_model: Optional[SentenceTransformer] = None

        # Cache data
        self.cached_embeddings: Dict[str, np.ndarray] = {}
        self.cached_metadata: Dict[str, Any] = {}

        # Load existing cache
        self._load_cache()

    def _get_default_cache_dir(self) -> Path:
        """Get default cache directory."""
        return Path(__file__).parent / ".embedding_cache"

    @property
    def embedding_model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self._embedding_model is None:
            try:
                self._embedding_model = SentenceTransformer(self.embedding_model_name)
                logger.info("Loaded embedding model: %s", self.embedding_model_name)
            except (OSError, ImportError, RuntimeError) as e:
                logger.error("Failed to load embedding model: %s", e)
                raise
        return self._embedding_model

    def _compute_example_hash(self, example: ToolExample) -> str:
        """Compute a hash for an example to detect changes."""
        # Create a deterministic representation of the example
        example_data = {
            "query": example.query,
            "tool_name": example.tool_name,
            "parameters": example.parameters,
            "context": example.context,
            "disambiguation_note": example.disambiguation_note,
            "tags": sorted(example.tags) if example.tags else [],
        }

        # Convert to JSON string and hash
        json_str = json.dumps(example_data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def _load_cache(self) -> None:
        """Load cached embeddings and metadata from disk."""
        try:
            # Load embeddings
            if self.embeddings_cache_file.exists():
                with open(self.embeddings_cache_file, "rb") as f:
                    self.cached_embeddings = pickle.load(f)
                logger.info("Loaded %d cached embeddings", len(self.cached_embeddings))

            # Load metadata
            if self.metadata_cache_file.exists():
                with open(self.metadata_cache_file, "r") as f:
                    self.cached_metadata = json.load(f)
                logger.info("Loaded embedding cache metadata")

        except (OSError, json.JSONDecodeError, pickle.PickleError) as e:
            logger.error("Failed to load embedding cache: %s", e)
            # Reset cache on error
            self.cached_embeddings = {}
            self.cached_metadata = {}

    def _save_cache(self) -> None:
        """Save cached embeddings and metadata to disk."""
        try:
            # Save embeddings
            with open(self.embeddings_cache_file, "wb") as f:
                pickle.dump(self.cached_embeddings, f)

            # Save metadata
            with open(self.metadata_cache_file, "w") as f:
                json.dump(self.cached_metadata, f, indent=2)

            logger.info("Saved %d embeddings to cache", len(self.cached_embeddings))

        except (OSError, TypeError, ValueError, pickle.PickleError) as e:
            logger.error("Failed to save embedding cache: %s", e)

    def get_or_compute_embeddings(
        self,
        examples: List[ToolExample],
        force_recompute: bool = False,
    ) -> List[ToolExample]:
        """Get embeddings for examples, computing and caching new ones as needed.

        Args:
            examples: List of examples to get embeddings for
            force_recompute: Whether to force recomputation of all embeddings

        Returns:
            List of examples with embeddings populated
        """
        examples_with_embeddings = []
        new_embeddings_needed = []
        new_embedding_indices = []

        # Check which examples need new embeddings
        for i, example in enumerate(examples):
            example_hash = self._compute_example_hash(example)

            if not force_recompute and example_hash in self.cached_embeddings:
                # Use cached embedding
                example.embedding = self.cached_embeddings[example_hash]
                examples_with_embeddings.append(example)
            else:
                # Need to compute new embedding
                new_embeddings_needed.append(example.query)
                new_embedding_indices.append((i, example_hash))
                examples_with_embeddings.append(example)

        # Compute new embeddings if needed
        if new_embeddings_needed:
            logger.info("Computing embeddings for %d new examples", len(new_embeddings_needed))

            try:
                new_embeddings = self.embedding_model.encode(new_embeddings_needed)

                # Update examples and cache
                for j, (example_idx, example_hash) in enumerate(new_embedding_indices):
                    embedding = new_embeddings[j]
                    examples_with_embeddings[example_idx].embedding = embedding
                    self.cached_embeddings[example_hash] = embedding

                # Update metadata
                self.cached_metadata.update(
                    {
                        "model_name": self.embedding_model_name,
                        "total_embeddings": len(self.cached_embeddings),
                        "last_updated": str(np.datetime64("now")),
                    }
                )

                # Save updated cache
                self._save_cache()

            except (RuntimeError, ValueError, OSError) as e:
                logger.error("Failed to compute new embeddings: %s", e)
                # Return examples without new embeddings
                pass

        return examples_with_embeddings

    def precompute_embeddings_from_files(
        self,
        examples_dir: Path,
        force_recompute: bool = False,
    ) -> None:
        """Precompute embeddings for all examples in JSON files.

        Args:
            examples_dir: Directory containing example JSON files
            force_recompute: Whether to force recomputation of all embeddings
        """
        if not examples_dir.exists():
            logger.warning("Examples directory not found: %s", examples_dir)
            return

        all_examples = []

        # Load all examples from JSON files
        for json_file in examples_dir.glob("*_examples.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)

                for example_data in data.get("examples", []):
                    example = ToolExample.from_dict(example_data)
                    all_examples.append(example)

                logger.info(
                    "Loaded %d examples from %s", len(data.get("examples", [])), json_file.name
                )

            except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error("Failed to load examples from %s: %s", json_file, e)

        if all_examples:
            logger.info("Precomputing embeddings for %d examples", len(all_examples))
            self.get_or_compute_embeddings(all_examples, force_recompute=force_recompute)
        else:
            logger.warning("No examples found to precompute embeddings for")

    def invalidate_cache(self) -> None:
        """Invalidate the entire cache."""
        self.cached_embeddings.clear()
        self.cached_metadata.clear()

        # Remove cache files
        try:
            if self.embeddings_cache_file.exists():
                self.embeddings_cache_file.unlink()
            if self.metadata_cache_file.exists():
                self.metadata_cache_file.unlink()
            logger.info("Invalidated embedding cache")
        except OSError as e:
            logger.error("Failed to invalidate cache: %s", e)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache."""
        cache_size_mb: float = 0.0
        if self.embeddings_cache_file.exists():
            cache_size_mb = self.embeddings_cache_file.stat().st_size / (1024 * 1024)

        return {
            "cached_embeddings": len(self.cached_embeddings),
            "cache_size_mb": round(cache_size_mb, 2),
            "model_name": self.cached_metadata.get("model_name", "unknown"),
            "last_updated": self.cached_metadata.get("last_updated", "never"),
            "cache_dir": str(self.cache_dir),
        }

    def cleanup_orphaned_embeddings(self, current_examples: List[ToolExample]) -> None:
        """Remove cached embeddings for examples that no longer exist.

        Args:
            current_examples: List of current examples
        """
        current_hashes = {self._compute_example_hash(ex) for ex in current_examples}
        cached_hashes = set(self.cached_embeddings.keys())

        orphaned_hashes = cached_hashes - current_hashes

        if orphaned_hashes:
            logger.info("Removing %d orphaned embeddings from cache", len(orphaned_hashes))
            for hash_key in orphaned_hashes:
                del self.cached_embeddings[hash_key]

            # Update metadata and save
            self.cached_metadata["total_embeddings"] = len(self.cached_embeddings)
            self._save_cache()


def precompute_all_embeddings(
    examples_dir: Optional[Path] = None,
    cache_dir: Optional[Path] = None,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    force_recompute: bool = False,
) -> None:
    """Utility function to precompute embeddings for all examples.

    Args:
        examples_dir: Directory containing example JSON files
        cache_dir: Directory to store cache files
        embedding_model: Name of the embedding model
        force_recompute: Whether to force recomputation of all embeddings
    """
    if examples_dir is None:
        examples_dir = Path(__file__).parent / "tool_examples"

    cache = EmbeddingCache(cache_dir=cache_dir, embedding_model_name=embedding_model)
    cache.precompute_embeddings_from_files(examples_dir, force_recompute=force_recompute)

    # Print cache statistics
    stats = cache.get_cache_stats()
    for key, value in stats.items():
        pass


if __name__ == "__main__":
    """Precompute embeddings for all examples."""
    import argparse

    parser = argparse.ArgumentParser(description="Precompute embeddings for examples")
    parser.add_argument("--examples-dir", type=Path, help="Directory containing example JSON files")
    parser.add_argument("--cache-dir", type=Path, help="Directory to store cache files")
    parser.add_argument(
        "--model", default="sentence-transformers/all-MiniLM-L6-v2", help="Embedding model name"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force recomputation of all embeddings"
    )

    args = parser.parse_args()

    precompute_all_embeddings(
        examples_dir=args.examples_dir,
        cache_dir=args.cache_dir,
        embedding_model=args.model,
        force_recompute=args.force,
    )
