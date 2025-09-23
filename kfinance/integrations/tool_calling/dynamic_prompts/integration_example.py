"""Example integration of dynamic prompt construction with existing tool calling pipeline."""

from __future__ import annotations

from typing import List, Optional, Set

from kfinance.client.permission_models import Permission
from kfinance.integrations.tool_calling.all_tools import ALL_TOOLS
from kfinance.integrations.tool_calling.dynamic_prompts import construct_dynamic_prompt
from kfinance.integrations.tool_calling.prompts import BASE_PROMPT


class EnhancedToolCaller:
    """Enhanced tool caller that uses dynamic prompt construction."""
    
    def __init__(
        self,
        user_permissions: Set[Permission],
        enable_dynamic_prompts: bool = True,
        fallback_to_static: bool = True,
    ):
        """Initialize the enhanced tool caller.
        
        Args:
            user_permissions: User's permissions for tool access
            enable_dynamic_prompts: Whether to use dynamic prompt construction
            fallback_to_static: Whether to fall back to static prompts on failure
        """
        self.user_permissions = user_permissions
        self.enable_dynamic_prompts = enable_dynamic_prompts
        self.fallback_to_static = fallback_to_static
        
        # Filter available tools based on permissions
        self.available_tools = self._filter_tools_by_permissions()
    
    def _filter_tools_by_permissions(self) -> List[str]:
        """Filter available tools based on user permissions."""
        available_tools = []
        
        for tool_class in ALL_TOOLS:
            # Check if user has required permissions for this tool
            if hasattr(tool_class, 'accepted_permissions') and tool_class.accepted_permissions:
                if tool_class.accepted_permissions.intersection(self.user_permissions):
                    available_tools.append(tool_class.name)
            else:
                # Tool doesn't require specific permissions
                available_tools.append(tool_class.name)
        
        return available_tools
    
    def get_prompt_for_query(self, query: str) -> str:
        """Get the appropriate prompt for a user query.
        
        Args:
            query: User query
            
        Returns:
            Prompt string (dynamic or static)
        """
        if not self.enable_dynamic_prompts:
            return BASE_PROMPT
        
        try:
            # Attempt dynamic prompt construction
            dynamic_prompt = construct_dynamic_prompt(
                query=query,
                user_permissions=self.user_permissions,
                available_tools=self.available_tools,
            )
            
            # Log the improvement (in practice, you'd use proper logging)
            static_tokens = len(BASE_PROMPT.split())
            dynamic_tokens = len(dynamic_prompt.split())
            print(f"Dynamic prompt: {dynamic_tokens} tokens vs static: {static_tokens} tokens")
            
            return dynamic_prompt
            
        except Exception as e:
            print(f"Dynamic prompt construction failed: {e}")
            
            if self.fallback_to_static:
                print("Falling back to static prompt")
                return BASE_PROMPT
            else:
                raise


def example_usage():
    """Example of how to use the enhanced tool caller."""
    
    # Initialize with user permissions
    user_permissions = {Permission.StatementsPermission}
    tool_caller = EnhancedToolCaller(user_permissions)
    
    # Test queries that benefit from dynamic prompts
    test_queries = [
        "What is the preferred stock additional paid in capital for Apple?",
        "Show me the total revenue for Google and Amazon",
        "Get quarterly revenue for Tesla in Q1 2023",
        "What are the total receivables for Microsoft?",
    ]
    
    print("=== Enhanced Tool Calling with Dynamic Prompts ===\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}: {query}")
        
        # Get dynamic prompt
        prompt = tool_caller.get_prompt_for_query(query)
        
        # In practice, you would now pass this prompt to your LLM
        # along with the available tools for the actual tool calling
        
        print(f"Prompt length: {len(prompt)} characters")
        print(f"Available tools: {len(tool_caller.available_tools)}")
        print("-" * 60)


def compare_static_vs_dynamic():
    """Compare static vs dynamic prompt approaches."""
    
    print("\n=== Static vs Dynamic Comparison ===\n")
    
    user_permissions = {Permission.StatementsPermission}
    
    # Test with a query that should benefit from examples
    query = "What is the preferred stock additional paid in capital for Apple?"
    
    # Static approach
    print("STATIC APPROACH:")
    print(f"Prompt: {BASE_PROMPT[:100]}...")
    print(f"Length: {len(BASE_PROMPT)} characters")
    print(f"Tokens: ~{len(BASE_PROMPT.split())}")
    print("Examples included: None (generic instructions only)")
    
    print("\nDYNAMIC APPROACH:")
    try:
        dynamic_prompt = construct_dynamic_prompt(
            query=query,
            user_permissions=user_permissions,
        )
        
        print(f"Prompt: {dynamic_prompt[:100]}...")
        print(f"Length: {len(dynamic_prompt)} characters")
        print(f"Tokens: ~{len(dynamic_prompt.split())}")
        
        # Count examples in dynamic prompt
        example_count = dynamic_prompt.count('Query: "')
        print(f"Examples included: {example_count} relevant examples")
        
        # Show token difference
        token_diff = len(dynamic_prompt.split()) - len(BASE_PROMPT.split())
        print(f"Token difference: {token_diff:+d} ({token_diff/len(BASE_PROMPT.split())*100:+.1f}%)")
        
    except Exception as e:
        print(f"Dynamic construction failed: {e}")
        print("This is expected if sentence-transformers is not installed")


def integration_with_existing_client():
    """Example of integrating with existing kfinance client."""
    
    print("\n=== Integration with Existing Client ===\n")
    
    # This is how you might modify the existing client to use dynamic prompts
    class EnhancedKFinanceClient:
        """Enhanced client with dynamic prompt support."""
        
        def __init__(self, user_permissions: Set[Permission]):
            self.user_permissions = user_permissions
            self.tool_caller = EnhancedToolCaller(user_permissions)
        
        def process_query(self, query: str) -> str:
            """Process a user query with dynamic prompts."""
            
            # Get the appropriate prompt
            prompt = self.tool_caller.get_prompt_for_query(query)
            
            # In the real implementation, you would:
            # 1. Pass the prompt to your LLM along with available tools
            # 2. Parse the LLM response to extract tool calls
            # 3. Execute the tools and return results
            
            return f"Processed query with {len(prompt.split())} token prompt"
    
    # Example usage
    client = EnhancedKFinanceClient({Permission.StatementsPermission})
    
    queries = [
        "What is the convertible preferred stock for Tesla?",
        "Show me the total debt to equity ratio for JPMorgan",
    ]
    
    for query in queries:
        result = client.process_query(query)
        print(f"Query: {query}")
        print(f"Result: {result}")
        print()


if __name__ == "__main__":
    """Run all examples."""
    
    try:
        example_usage()
        compare_static_vs_dynamic()
        integration_with_existing_client()
        
        print("\n✅ Integration examples completed!")
        print("\nNext steps for full integration:")
        print("1. Install sentence-transformers: pip install sentence-transformers")
        print("2. Modify existing tool calling pipeline to use EnhancedToolCaller")
        print("3. Add more examples for other tools beyond line_items")
        print("4. Run evaluation to measure improvements")
        print("5. Consider A/B testing with real users")
        
    except Exception as e:
        print(f"❌ Integration example failed: {e}")
        print("\nThis is expected if dependencies are not installed.")
        import traceback
        traceback.print_exc()
