"""Demonstration script for dynamic prompt construction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Set

from kfinance.client.permission_models import Permission
from .integration import DynamicPromptManager


def demo_dynamic_prompt_construction():
    """Demonstrate dynamic prompt construction with various queries."""
    
    print("=== Dynamic Prompt Construction Demo ===\n")
    
    # Initialize the dynamic prompt manager with caching enabled
    manager = DynamicPromptManager(enable_caching=True)
    
    # Show cache statistics
    cache_stats = manager.get_cache_stats()
    if "error" not in cache_stats:
        print("Cache Statistics:")
        for key, value in cache_stats.items():
            print(f"  {key}: {value}")
        print()
    
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
    
    print("Testing dynamic prompt construction with various queries:\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"--- Test Query {i} ---")
        print(f"Query: {query}")
        
        # Construct dynamic prompt with statistics
        prompt, stats = manager.get_prompt_with_stats(
            query=query,
            user_permissions=user_permissions,
        )
        
        print(f"Prompt Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Show relevant examples found
        similar_examples = manager.search_similar_examples(
            query=query,
            user_permissions=user_permissions,
            top_k=3,
        )
        
        if similar_examples:
            print(f"Top {len(similar_examples)} similar examples:")
            for j, example in enumerate(similar_examples, 1):
                print(f"  {j}. {example['query']} (similarity: {example['similarity_score']:.3f})")
        else:
            print("No similar examples found")
        
        print("\n" + "="*80 + "\n")
    
    # Show repository statistics
    repo_stats = manager.get_repository_stats()
    print("Repository Statistics:")
    print(json.dumps(repo_stats, indent=2))


def demo_prompt_comparison():
    """Compare static vs dynamic prompts for specific queries."""
    
    print("\n=== Static vs Dynamic Prompt Comparison ===\n")
    
    # Import base prompt for comparison
    from kfinance.integrations.tool_calling.prompts import BASE_PROMPT
    
    manager = DynamicPromptManager()
    user_permissions: Set[Permission] = {Permission.StatementsPermission}
    
    # Test with a query that should benefit from dynamic examples
    test_query = "What is the preferred stock additional paid in capital for Apple?"
    
    print(f"Test Query: {test_query}\n")
    
    # Static prompt
    print("--- STATIC PROMPT ---")
    print(f"Length: {len(BASE_PROMPT)} characters")
    print(f"Lines: {len(BASE_PROMPT.split())}")
    print("Content preview:")
    print(BASE_PROMPT[:200] + "..." if len(BASE_PROMPT) > 200 else BASE_PROMPT)
    
    print("\n" + "="*50 + "\n")
    
    # Dynamic prompt
    print("--- DYNAMIC PROMPT ---")
    dynamic_prompt, stats = manager.get_prompt_with_stats(
        query=test_query,
        user_permissions=user_permissions,
    )
    
    print(f"Statistics: {stats}")
    print("Content preview:")
    print(dynamic_prompt[:500] + "..." if len(dynamic_prompt) > 500 else dynamic_prompt)
    
    # Show the difference in token usage (approximate)
    static_tokens = len(BASE_PROMPT.split())
    dynamic_tokens = len(dynamic_prompt.split())
    
    print(f"\nToken Usage Comparison:")
    print(f"Static prompt: ~{static_tokens} tokens")
    print(f"Dynamic prompt: ~{dynamic_tokens} tokens")
    print(f"Difference: {dynamic_tokens - static_tokens:+d} tokens ({((dynamic_tokens - static_tokens) / static_tokens * 100):+.1f}%)")


def demo_parameter_disambiguation():
    """Demonstrate how the system helps with parameter disambiguation."""
    
    print("\n=== Parameter Disambiguation Demo ===\n")
    
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
        print(f"--- Disambiguation Test {i} ---")
        print(f"Query: {test['query']}")
        print(f"Correct parameter: {test['correct_param']}")
        print(f"Common mistake: {test['common_mistake']}")
        
        # Find similar examples
        similar_examples = manager.search_similar_examples(
            query=test['query'],
            user_permissions=user_permissions,
            top_k=2,
        )
        
        if similar_examples:
            print("Relevant examples that should help disambiguation:")
            for example in similar_examples:
                if test['correct_param'] in str(example.get('parameters', {})):
                    print(f"  ✓ Found example using correct parameter: {test['correct_param']}")
                    if example.get('disambiguation_note'):
                        print(f"    Note: {example['disambiguation_note']}")
                    break
        
        print()


def demo_permission_filtering():
    """Demonstrate how permission filtering works."""
    
    print("\n=== Permission Filtering Demo ===\n")
    
    manager = DynamicPromptManager()
    
    # Test with different permission sets
    permission_sets = [
        {Permission.StatementsPermission},
        {Permission.StatementsPermission, Permission.PrivateCompanyFinancialsPermission},
        set(),  # No permissions
    ]
    
    test_query = "What is the revenue for Apple?"
    
    for i, permissions in enumerate(permission_sets, 1):
        print(f"--- Permission Set {i}: {[p.value for p in permissions] if permissions else 'None'} ---")
        
        similar_examples = manager.search_similar_examples(
            query=test_query,
            user_permissions=permissions,
            top_k=5,
        )
        
        print(f"Found {len(similar_examples)} examples accessible with these permissions")
        
        if similar_examples:
            for example in similar_examples[:2]:  # Show first 2
                required_perms = example.get('permissions_required', [])
                print(f"  - Example requires: {required_perms}")
        
        print()


def demo_embedding_cache():
    """Demonstrate embedding cache functionality."""
    
    print("\n=== Embedding Cache Demo ===\n")
    
    # Initialize manager with caching
    manager = DynamicPromptManager(enable_caching=True)
    
    print("1. Initial cache statistics:")
    stats = manager.get_cache_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test query to trigger embedding computation
    test_query = "What is the preferred stock additional paid in capital for Apple?"
    user_permissions = {Permission.StatementsPermission}
    
    print(f"\n2. Testing query: {test_query}")
    
    # First call - may compute embeddings
    import time
    start_time = time.time()
    prompt1, stats1 = manager.get_prompt_with_stats(test_query, user_permissions)
    first_call_time = time.time() - start_time
    
    print(f"   First call time: {first_call_time:.3f} seconds")
    print(f"   Examples found: {stats1.get('example_count', 0)}")
    
    # Second call - should use cached embeddings
    start_time = time.time()
    prompt2, stats2 = manager.get_prompt_with_stats(test_query, user_permissions)
    second_call_time = time.time() - start_time
    
    print(f"   Second call time: {second_call_time:.3f} seconds")
    print(f"   Examples found: {stats2.get('example_count', 0)}")
    
    if first_call_time > 0:
        speedup = first_call_time / second_call_time if second_call_time > 0 else float('inf')
        print(f"   Speedup: {speedup:.1f}x")
    
    # Show updated cache statistics
    print("\n3. Updated cache statistics:")
    updated_stats = manager.get_cache_stats()
    for key, value in updated_stats.items():
        print(f"   {key}: {value}")
    
    # Demonstrate precomputation
    print("\n4. Precomputing all embeddings...")
    if manager.precompute_embeddings():
        print("   ✅ Precomputation successful")
        
        final_stats = manager.get_cache_stats()
        print("   Final cache statistics:")
        for key, value in final_stats.items():
            print(f"     {key}: {value}")
    else:
        print("   ❌ Precomputation failed")


if __name__ == "__main__":
    """Run all demonstrations."""
    try:
        demo_dynamic_prompt_construction()
        demo_prompt_comparison()
        demo_parameter_disambiguation()
        demo_permission_filtering()
        demo_embedding_cache()
        
        print("\n🎉 Demo completed successfully!")
        print("\nNext steps:")
        print("1. Install sentence-transformers: pip install sentence-transformers")
        print("2. Precompute embeddings: python -m kfinance.integrations.tool_calling.dynamic_prompts.cli precompute")
        print("3. Create more example files for other tools")
        print("4. Integrate with actual tool calling pipeline")
        print("5. Run evaluation tests to measure improvement")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        print("\nThis is expected if dependencies are not installed.")
        print("Install sentence-transformers: pip install sentence-transformers")
        import traceback
        traceback.print_exc()
