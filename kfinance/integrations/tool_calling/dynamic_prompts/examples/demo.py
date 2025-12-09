"""Demonstration of dynamic prompt construction capabilities."""

import logging
import time
from typing import Set

from kfinance.client.permission_models import Permission
from kfinance.integrations.tool_calling.prompts import BASE_PROMPT

from ..core.manager import DynamicPromptManager


logger = logging.getLogger(__name__)


def demo_dynamic_prompt_construction() -> None:
    """Demonstrate dynamic prompt construction with various queries."""

    # Initialize the dynamic prompt manager with caching enabled
    manager = DynamicPromptManager(enable_caching=True)

    # Show cache statistics
    logger.info("Initial Cache Statistics:")
    cache_stats = manager.get_cache_stats()
    if "error" not in cache_stats:
        for key, value in cache_stats.items():
            logger.info("  %s: %s", key, value)
    else:
        logger.info("  Cache not available or error occurred")

    # Example user permissions (assuming user has statements permission)
    user_permissions: Set[Permission] = {Permission.StatementsPermission}

    # Test queries that should trigger different examples
    test_queries = [
        "What is the preferred stock additional paid in capital for Apple?",
        "Show me the total revenue for Google and Amazon",
        "Get quarterly revenue for Tesla in Q1 2023",
        "What are the total receivables for Microsoft?",
        "Show me depreciation and amortization for Ford",
        "What is the debt to equity ratio for JPMorgan?",
        "Get the convertible preferred stock for Netflix",
    ]

    for i, query in enumerate(test_queries, 1):
        logger.info("Test Query %d: %s", i, query)
        logger.info("-" * 60)

        # Construct dynamic prompt with statistics
        prompt, stats = manager.get_prompt_with_stats(
            query=query,
            user_permissions=user_permissions,
        )

        logger.info("Prompt Stats:")
        for key, value in stats.items():
            logger.info("  %s: %s", key, value)

        # Show relevant examples found
        similar_examples = manager.search_similar_examples(
            query=query,
            user_permissions=user_permissions,
            top_k=3,
        )

        logger.info("Similar Examples:")
        if similar_examples:
            for j, example in enumerate(similar_examples, 1):
                similarity = example.get("similarity_score", 0)
                example_query = example.get("query", "Unknown")
                logger.info("  %d. %s (similarity: %.3f)", j, example_query, similarity)
        else:
            logger.info("  No similar examples found")

    # Show repository statistics
    logger.info("Final Repository Statistics:")
    repo_stats = manager.get_repository_stats()
    for key, value in repo_stats.items():
        if isinstance(value, dict):
            logger.info("  %s:", key)
            for sub_key, sub_value in value.items():
                logger.info("    %s: %s", sub_key, sub_value)
        else:
            logger.info("  %s: %s", key, value)


def demo_prompt_comparison() -> None:
    """Compare static vs dynamic prompts for specific queries."""

    logger.info("Comparing Static vs Dynamic Prompts")
    logger.info("=" * 50)

    # Use base prompt for comparison
    manager = DynamicPromptManager()
    user_permissions: Set[Permission] = {Permission.StatementsPermission}

    # Test with a query that should benefit from dynamic examples
    test_query = "What is the preferred stock additional paid in capital for Apple?"

    # Dynamic prompt
    dynamic_prompt, stats = manager.get_prompt_with_stats(
        query=test_query,
        user_permissions=user_permissions,
    )

    # Show the difference in token usage (approximate)
    base_tokens = len(BASE_PROMPT.split())
    dynamic_tokens = len(dynamic_prompt.split())

    logger.info("Token Comparison:")
    logger.info("  Base prompt tokens: %d", base_tokens)
    logger.info("  Dynamic prompt tokens: %d", dynamic_tokens)
    logger.info(
        "  Token difference: %d (%.1f%% change)",
        dynamic_tokens - base_tokens,
        ((dynamic_tokens - base_tokens) / base_tokens * 100) if base_tokens > 0 else 0,
    )


def demo_parameter_disambiguation() -> None:
    """Demonstrate how the system helps with parameter disambiguation."""

    manager = DynamicPromptManager()
    user_permissions: Set[Permission] = {Permission.StatementsPermission}

    # Queries that commonly cause parameter confusion
    disambiguation_tests = [
        {
            "query": "What is the convertible preferred stock for Tesla?",
            "correct_param": "preferred_stock_convertible",
            "common_mistake": "convertible_preferred_stock",
        },
        {
            "query": "Show me the total debt to equity ratio for JPMorgan",
            "correct_param": "total_debt_to_equity",
            "common_mistake": "total_debt_to_equity_ratio",
        },
        {
            "query": "Get the total receivables for Microsoft",
            "correct_param": "total_receivable",
            "common_mistake": "total_receivables",
        },
    ]

    logger.info("Parameter Disambiguation Demo")
    logger.info("=" * 50)

    for i, test in enumerate(disambiguation_tests, 1):
        logger.info("Test %d: %s", i, test["query"])
        logger.info("  Correct parameter: %s", test["correct_param"])
        logger.info("  Common mistake: %s", test["common_mistake"])

        # Find similar examples
        similar_examples = manager.search_similar_examples(
            query=test["query"],
            user_permissions=user_permissions,
            top_k=2,
        )

        if similar_examples:
            logger.info("  Similar examples found:")
            for example in similar_examples:
                if test["correct_param"] in str(example.get("parameters", {})):
                    if example.get("disambiguation_note"):
                        logger.info(
                            "    Found disambiguation guidance: %s",
                            example.get("disambiguation_note"),
                        )
                    else:
                        logger.info("    Found correct parameter usage: %s", test["correct_param"])
                    break


def demo_permission_filtering() -> None:
    """Demonstrate how permission filtering works."""

    manager = DynamicPromptManager()

    # Test with different permission sets
    permission_sets = [
        {Permission.StatementsPermission},
        {Permission.StatementsPermission, Permission.PrivateCompanyFinancialsPermission},
        set(),  # No permissions
    ]

    test_query = "What is the revenue for Apple?"

    logger.info("Permission Filtering Demo")
    logger.info("=" * 50)

    for i, permissions in enumerate(permission_sets, 1):
        perm_names = [p.name for p in permissions] if permissions else ["No permissions"]
        logger.info("Test %d - Permissions: %s", i, ", ".join(perm_names))

        similar_examples = manager.search_similar_examples(
            query=test_query,
            user_permissions=permissions,
            top_k=5,
        )

        if similar_examples:
            logger.info("  Found %d examples:", len(similar_examples))
            for example in similar_examples[:2]:  # Show first 2
                required_perms = example.get("permissions_required", [])
                example_query = example.get("query", "Unknown")
                logger.info("    - %s (requires: %s)", example_query, required_perms)
        else:
            logger.info("  No examples found with these permissions")


def demo_embedding_cache() -> None:
    """Demonstrate embedding cache functionality."""

    # Initialize manager with caching
    manager = DynamicPromptManager(enable_caching=True)

    logger.info("Initial Cache Stats:")
    stats = manager.get_cache_stats()
    for key, value in stats.items():
        logger.info("  %s: %s", key, value)

    # Test query to trigger embedding computation
    test_query = "What is the preferred stock additional paid in capital for Apple?"
    user_permissions = {Permission.StatementsPermission}

    # First call - may compute embeddings
    logger.info("First call (may compute embeddings)...")
    start_time = time.time()
    prompt1, stats1 = manager.get_prompt_with_stats(test_query, user_permissions)
    first_call_time = time.time() - start_time

    # Second call - should use cached embeddings
    logger.info("Second call (should use cache)...")
    start_time = time.time()
    prompt2, stats2 = manager.get_prompt_with_stats(test_query, user_permissions)
    second_call_time = time.time() - start_time

    if first_call_time > 0:
        speedup = first_call_time / second_call_time if second_call_time > 0 else float("inf")
        logger.info("Performance Comparison:")
        logger.info("  First call: %.3fs", first_call_time)
        logger.info("  Second call: %.3fs", second_call_time)
        logger.info("  Speedup: %.1fx", speedup)

    # Show updated cache statistics
    logger.info("Updated Cache Stats:")
    updated_stats = manager.get_cache_stats()
    for key, value in updated_stats.items():
        logger.info("  %s: %s", key, value)

    # Demonstrate precomputation
    logger.info("Precomputing embeddings...")
    if manager.precompute_embeddings():
        logger.info("  Precomputation successful")
        final_stats = manager.get_cache_stats()
        logger.info("Final Cache Stats:")
        for key, value in final_stats.items():
            logger.info("  %s: %s", key, value)
    else:
        logger.info("  Precomputation failed")


if __name__ == "__main__":
    """Run all demonstrations."""
    try:
        demo_dynamic_prompt_construction()
        demo_prompt_comparison()
        demo_parameter_disambiguation()
        demo_permission_filtering()
        demo_embedding_cache()

    except (RuntimeError, ValueError, OSError, ImportError):
        import traceback

        traceback.print_exc()
