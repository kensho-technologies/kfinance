"""Example integration of dynamic prompt construction with existing tool calling pipeline."""

from __future__ import annotations

from typing import List, Set

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
            if hasattr(tool_class, "accepted_permissions") and tool_class.accepted_permissions:
                if tool_class.accepted_permissions.intersection(self.user_permissions):
                    available_tools.append(tool_class.__name__)
            else:
                # Tool doesn't require specific permissions
                available_tools.append(tool_class.__name__)

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
            )

            # Log the improvement (in practice, you'd use proper logging)
            len(BASE_PROMPT.split())
            len(dynamic_prompt.split())

            return dynamic_prompt

        except (RuntimeError, ValueError, OSError, ImportError):
            if self.fallback_to_static:
                return BASE_PROMPT
            else:
                raise


def example_usage() -> None:
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

    for i, query in enumerate(test_queries, 1):
        # Get dynamic prompt
        tool_caller.get_prompt_for_query(query)

        # In practice, you would now pass this prompt to your LLM
        # along with the available tools for the actual tool calling


def compare_static_vs_dynamic() -> None:
    """Compare static vs dynamic prompt approaches."""

    user_permissions = {Permission.StatementsPermission}

    # Test with a query that should benefit from examples
    query = "What is the preferred stock additional paid in capital for Apple?"

    # Static approach

    try:
        dynamic_prompt = construct_dynamic_prompt(
            query=query,
            user_permissions=user_permissions,
        )

        # Count examples in dynamic prompt
        dynamic_prompt.count('Query: "')

        # Show token difference
        len(dynamic_prompt.split()) - len(BASE_PROMPT.split())

    except (RuntimeError, ValueError, OSError, ImportError):
        pass


def integration_with_existing_client() -> None:
    """Example of integrating with existing kfinance client."""

    # This is how you might modify the existing client to use dynamic prompts
    class EnhancedKFinanceClient:
        """Enhanced client with dynamic prompt support."""

        def __init__(self, user_permissions: Set[Permission]) -> None:
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
        client.process_query(query)


if __name__ == "__main__":
    """Run all examples."""

    try:
        example_usage()
        compare_static_vs_dynamic()
        integration_with_existing_client()

    except (RuntimeError, ValueError, OSError, ImportError):
        import traceback

        traceback.print_exc()
