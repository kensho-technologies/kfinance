"""Command-line interface for managing dynamic prompt embeddings."""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .embedding_cache import precompute_all_embeddings
from .integration import DynamicPromptManager


def precompute_command(args: argparse.Namespace) -> None:
    """Precompute embeddings for all examples."""
    print("🔄 Precomputing embeddings...")
    
    try:
        precompute_all_embeddings(
            examples_dir=args.examples_dir,
            cache_dir=args.cache_dir,
            embedding_model=args.model,
            force_recompute=args.force,
        )
        print("✅ Successfully precomputed embeddings!")
        
    except Exception as e:
        print(f"❌ Failed to precompute embeddings: {e}")
        sys.exit(1)


def stats_command(args: argparse.Namespace) -> None:
    """Show cache and repository statistics."""
    print("📊 Dynamic Prompt Statistics")
    print("=" * 40)
    
    try:
        manager = DynamicPromptManager(
            examples_dir=args.examples_dir,
            cache_dir=args.cache_dir,
            embedding_model=args.model,
        )
        
        stats = manager.get_repository_stats()
        
        # Repository stats
        print(f"Total examples: {stats.get('total_examples', 0)}")
        print(f"Parameter descriptors: {stats.get('total_parameter_descriptors', 0)}")
        print(f"Tools with descriptors: {stats.get('tools_with_descriptors', 0)}")
        
        # Examples by tool
        examples_by_tool = stats.get('examples_by_tool', {})
        if examples_by_tool:
            print("\nExamples by tool:")
            for tool, count in examples_by_tool.items():
                print(f"  {tool}: {count}")
        
        # Cache stats
        cache_stats = stats.get('cache', {})
        if cache_stats and 'error' not in cache_stats:
            print(f"\nCache Statistics:")
            print(f"  Cached embeddings: {cache_stats.get('cached_embeddings', 0)}")
            print(f"  Cache size: {cache_stats.get('cache_size_mb', 0)} MB")
            print(f"  Model: {cache_stats.get('model_name', 'unknown')}")
            print(f"  Last updated: {cache_stats.get('last_updated', 'never')}")
            print(f"  Cache directory: {cache_stats.get('cache_dir', 'unknown')}")
        else:
            print("\n⚠️  No cache statistics available")
        
    except Exception as e:
        print(f"❌ Failed to get statistics: {e}")
        sys.exit(1)


def invalidate_command(args: argparse.Namespace) -> None:
    """Invalidate the embedding cache."""
    print("🗑️  Invalidating embedding cache...")
    
    try:
        manager = DynamicPromptManager(
            examples_dir=args.examples_dir,
            cache_dir=args.cache_dir,
            embedding_model=args.model,
        )
        
        if manager.invalidate_cache():
            print("✅ Successfully invalidated cache!")
        else:
            print("❌ Failed to invalidate cache")
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ Failed to invalidate cache: {e}")
        sys.exit(1)


def test_command(args: argparse.Namespace) -> None:
    """Test dynamic prompt construction with a sample query."""
    print("🧪 Testing dynamic prompt construction...")
    
    try:
        from kfinance.client.permission_models import Permission
        
        manager = DynamicPromptManager(
            examples_dir=args.examples_dir,
            cache_dir=args.cache_dir,
            embedding_model=args.model,
        )
        
        # Test query
        test_query = args.query or "What is the preferred stock additional paid in capital for Apple?"
        user_permissions = {Permission.StatementsPermission}
        
        print(f"Query: {test_query}")
        
        # Show entity normalization
        try:
            # Access the repository to get the entity normalizer
            manager._initialize()  # Ensure repository is loaded
            if hasattr(manager._repository, 'normalize_query_for_search'):
                normalized_query, entity_mapping = manager._repository.normalize_query_for_search(test_query)
                if entity_mapping:
                    print(f"Normalized: {normalized_query}")
                    print(f"Entity mapping: {entity_mapping}")
                else:
                    print("Normalized: (no entities detected)")
        except Exception as e:
            print(f"Entity normalization: (error: {e})")
        
        print("-" * 60)
        
        # Get prompt with stats
        prompt, stats = manager.get_prompt_with_stats(
            query=test_query,
            user_permissions=user_permissions,
        )
        
        print("Prompt Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Show similar examples
        similar_examples = manager.search_similar_examples(
            query=test_query,
            user_permissions=user_permissions,
            top_k=3,
        )
        
        if similar_examples:
            print(f"\nTop {len(similar_examples)} similar examples:")
            for i, example in enumerate(similar_examples, 1):
                similarity = example.get('similarity_score', 0)
                query_text = example.get('query', 'Unknown')
                print(f"  {i}. {query_text} (similarity: {similarity:.3f})")
        else:
            print("\nNo similar examples found")
        
        if args.show_prompt:
            print(f"\nGenerated Prompt (first 500 chars):")
            print("-" * 60)
            print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Dynamic Prompt Construction CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Precompute embeddings for all examples
  python -m kfinance.integrations.tool_calling.dynamic_prompts.cli precompute
  
  # Show statistics
  python -m kfinance.integrations.tool_calling.dynamic_prompts.cli stats
  
  # Test with a custom query
  python -m kfinance.integrations.tool_calling.dynamic_prompts.cli test --query "What is the revenue for Apple?"
  
  # Force recompute all embeddings
  python -m kfinance.integrations.tool_calling.dynamic_prompts.cli precompute --force
        """
    )
    
    # Global arguments
    parser.add_argument(
        "--examples-dir", 
        type=Path, 
        help="Directory containing example JSON files"
    )
    parser.add_argument(
        "--cache-dir", 
        type=Path, 
        help="Directory to store cache files"
    )
    parser.add_argument(
        "--model", 
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Embedding model name"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Precompute command
    precompute_parser = subparsers.add_parser(
        "precompute", 
        help="Precompute embeddings for all examples"
    )
    precompute_parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force recomputation of all embeddings"
    )
    
    # Stats command
    subparsers.add_parser("stats", help="Show cache and repository statistics")
    
    # Invalidate command
    subparsers.add_parser("invalidate", help="Invalidate the embedding cache")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test dynamic prompt construction with entity normalization")
    test_parser.add_argument(
        "--query", 
        help="Query to test with (default: sample query). Shows entity normalization using spaCy NER."
    )
    test_parser.add_argument(
        "--show-prompt", 
        action="store_true", 
        help="Show the generated prompt"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == "precompute":
        precompute_command(args)
    elif args.command == "stats":
        stats_command(args)
    elif args.command == "invalidate":
        invalidate_command(args)
    elif args.command == "test":
        test_command(args)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
