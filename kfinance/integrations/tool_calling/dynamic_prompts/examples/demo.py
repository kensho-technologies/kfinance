"""Demonstration script for dynamic prompt construction."""

from __future__ import annotations

from typing import Set

from kfinance.client.permission_models import Permission

from .integration import DynamicPromptManager


def demo_dynamic_prompt_construction() -> None:
    """Demonstrate dynamic prompt construction with various queries."""


    # Initialize the dynamic prompt manager with caching enabled
    manager = DynamicPromptManager(enable_caching=True)

    # Show cache statistics
    cache_stats = manager.get_cache_stats()
    if "error" not in cache_stats:
        for key, value in cache_stats.items():
            pass

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

        # Construct dynamic prompt with statistics
        prompt, stats = manager.get_prompt_with_stats(
            query=query,
            user_permissions=user_permissions,
        )

        for key, value in stats.items():
            pass

        # Show relevant examples found
        similar_examples = manager.search_similar_examples(
            query=query,
            user_permissions=user_permissions,
            top_k=3,
        )

        if similar_examples:
            for j, example in enumerate(similar_examples, 1):
                pass
        else:
            pass


    # Show repository statistics
    manager.get_repository_stats()


def demo_prompt_comparison() -> None:
    """Compare static vs dynamic prompts for specific queries."""


    # Import base prompt for comparison
    from kfinance.integrations.tool_calling.prompts import BASE_PROMPT

    manager = DynamicPromptManager()
    user_permissions: Set[Permission] = {Permission.StatementsPermission}

    # Test with a query that should benefit from dynamic examples
    test_query = "What is the preferred stock additional paid in capital for Apple?"


    # Static prompt


    # Dynamic prompt
    dynamic_prompt, stats = manager.get_prompt_with_stats(
        query=test_query,
        user_permissions=user_permissions,
    )


    # Show the difference in token usage (approximate)
    len(BASE_PROMPT.split())
    len(dynamic_prompt.split())



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

    for i, test in enumerate(disambiguation_tests, 1):

        # Find similar examples
        similar_examples = manager.search_similar_examples(
            query=test["query"],
            user_permissions=user_permissions,
            top_k=2,
        )

        if similar_examples:
            for example in similar_examples:
                if test["correct_param"] in str(example.get("parameters", {})):
                    if example.get("disambiguation_note"):
                        pass
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

    for i, permissions in enumerate(permission_sets, 1):

        similar_examples = manager.search_similar_examples(
            query=test_query,
            user_permissions=permissions,
            top_k=5,
        )


        if similar_examples:
            for example in similar_examples[:2]:  # Show first 2
                example.get("permissions_required", [])



def demo_embedding_cache() -> None:
    """Demonstrate embedding cache functionality."""


    # Initialize manager with caching
    manager = DynamicPromptManager(enable_caching=True)

    stats = manager.get_cache_stats()
    for key, value in stats.items():
        pass

    # Test query to trigger embedding computation
    test_query = "What is the preferred stock additional paid in capital for Apple?"
    user_permissions = {Permission.StatementsPermission}


    # First call - may compute embeddings
    import time
    start_time = time.time()
    prompt1, stats1 = manager.get_prompt_with_stats(test_query, user_permissions)
    first_call_time = time.time() - start_time


    # Second call - should use cached embeddings
    start_time = time.time()
    prompt2, stats2 = manager.get_prompt_with_stats(test_query, user_permissions)
    second_call_time = time.time() - start_time


    if first_call_time > 0:
        first_call_time / second_call_time if second_call_time > 0 else float("inf")

    # Show updated cache statistics
    updated_stats = manager.get_cache_stats()
    for key, value in updated_stats.items():
        pass

    # Demonstrate precomputation
    if manager.precompute_embeddings():

        final_stats = manager.get_cache_stats()
        for key, value in final_stats.items():
            pass
    else:
        pass


if __name__ == "__main__":
    """Run all demonstrations."""
    try:
        demo_dynamic_prompt_construction()
        demo_prompt_comparison()
        demo_parameter_disambiguation()
        demo_permission_filtering()
        demo_embedding_cache()


    except Exception:
        import traceback
        traceback.print_exc()
