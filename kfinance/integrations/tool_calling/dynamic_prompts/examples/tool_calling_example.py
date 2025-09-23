"""Complete example of using dynamic prompt construction with tool calling."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from kfinance.client.permission_models import Permission
from kfinance.integrations.tool_calling.dynamic_prompts.core.manager import DynamicPromptManager
from kfinance.integrations.tool_calling.prompts import BASE_PROMPT


# Mock LLM client for demonstration (replace with your actual LLM client)
class MockLLMClient:
    """Mock LLM client for demonstration purposes."""

    def __init__(self) -> None:
        """Initialize the mock LLM client."""
        self.call_count = 0

    def generate_with_tools(self, prompt: str, available_tools: List[Dict]) -> Dict[str, Any]:
        """Mock LLM generation with tool calling."""
        self.call_count += 1

        # Simulate LLM response based on prompt content
        if "preferred stock additional paid in capital" in prompt.lower():
            return {
                "tool_calls": [
                    {
                        "name": "get_financial_line_item_from_identifiers",
                        "parameters": {
                            "identifiers": ["AAPL"],
                            "line_item": "additional_paid_in_capital_preferred_stock",
                        },
                    }
                ],
                "reasoning": "Based on the examples provided, I should use 'additional_paid_in_capital_preferred_stock' for preferred stock capital above par value.",
            }
        elif "convertible preferred stock" in prompt.lower():
            return {
                "tool_calls": [
                    {
                        "name": "get_financial_line_item_from_identifiers",
                        "parameters": {
                            "identifiers": ["TSLA"],
                            "line_item": "preferred_stock_convertible",
                        },
                    }
                ],
                "reasoning": "The examples show to use 'preferred_stock_convertible' not 'convertible_preferred_stock'.",
            }
        else:
            return {
                "tool_calls": [
                    {
                        "name": "get_financial_line_item_from_identifiers",
                        "parameters": {"identifiers": ["AAPL"], "line_item": "revenue"},
                    }
                ],
                "reasoning": "Generic revenue query.",
            }


# Mock tool execution (replace with your actual tool implementations)
def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Mock tool execution for demonstration."""
    if tool_name == "get_financial_line_item_from_identifiers":
        line_item = parameters.get("line_item", "unknown")
        identifiers = parameters.get("identifiers", [])

        # Mock financial data
        mock_data = {
            "additional_paid_in_capital_preferred_stock": 1250000000,
            "preferred_stock_convertible": 850000000,
            "revenue": 394328000000,
            "total_revenue": 394328000000,
        }

        value = mock_data.get(line_item, 0)

        return {
            "success": True,
            "data": {
                "line_item": line_item,
                "identifiers": identifiers,
                "value": value,
                "currency": "USD",
                "period": "2023",
            },
        }

    return {"success": False, "error": f"Unknown tool: {tool_name}"}


class EnhancedFinancialQueryProcessor:
    """Enhanced financial query processor using dynamic prompts."""

    def __init__(
        self,
        user_permissions: Set[Permission],
        llm_client: Optional[MockLLMClient] = None,
        enable_dynamic_prompts: bool = True,
    ):
        """Initialize the query processor.

        Args:
            user_permissions: User's permissions for tool access
            llm_client: LLM client for generating responses
            enable_dynamic_prompts: Whether to use dynamic prompt construction
        """
        self.user_permissions = user_permissions
        self.llm_client = llm_client or MockLLMClient()
        self.enable_dynamic_prompts = enable_dynamic_prompts

        # Initialize dynamic prompt manager
        self.prompt_manager = (
            DynamicPromptManager(enable_caching=True) if enable_dynamic_prompts else None
        )

        # Available tools (simplified for demo)
        self.available_tools = [
            {
                "name": "get_financial_line_item_from_identifiers",
                "description": "Get financial line items for companies by identifiers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "identifiers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Company identifiers (tickers)",
                        },
                        "line_item": {
                            "type": "string",
                            "description": "Financial line item to retrieve",
                        },
                        "period_type": {
                            "type": "string",
                            "enum": ["annual", "quarterly"],
                            "description": "Period type for data",
                        },
                    },
                    "required": ["identifiers", "line_item"],
                },
            }
        ]

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a financial query using dynamic prompts and tool calling.

        Args:
            query: User's financial query

        Returns:
            Dictionary with results and metadata
        """

        # Step 1: Construct dynamic prompt or use static prompt
        if self.enable_dynamic_prompts and self.prompt_manager:
            prompt, stats = self.prompt_manager.get_prompt_with_stats(
                query=query,
                user_permissions=self.user_permissions,
            )

            # Show similar examples found
            similar_examples = self.prompt_manager.search_similar_examples(
                query=query,
                user_permissions=self.user_permissions,
                top_k=3,
            )

            if similar_examples:
                for i, example in enumerate(similar_examples[:2], 1):
                    example.get("similarity_score", 0)
                    example.get("query", "Unknown")
        else:
            prompt = BASE_PROMPT
            stats = {"example_count": 0, "total_words": len(prompt.split())}

        # Step 2: Generate LLM response with tool calling

        llm_response = self.llm_client.generate_with_tools(
            prompt=prompt, available_tools=self.available_tools
        )

        # Step 3: Execute tool calls
        results = []
        tool_calls = llm_response.get("tool_calls", [])

        if tool_calls:
            for i, tool_call in enumerate(tool_calls, 1):
                tool_name = tool_call["name"]
                parameters = tool_call["parameters"]

                # Execute the tool
                tool_result = execute_tool(tool_name, parameters)
                results.append(
                    {"tool_name": tool_name, "parameters": parameters, "result": tool_result}
                )

                if tool_result.get("success"):
                    data = tool_result.get("data", {})
                    data.get("value", "N/A")
                    data.get("line_item", "unknown")
                else:
                    pass
        else:
            pass

        # Step 4: Return comprehensive results
        return {
            "query": query,
            "prompt_stats": stats,
            "llm_response": llm_response,
            "tool_results": results,
            "success": len([r for r in results if r["result"].get("success")]) > 0,
        }


def demo_basic_usage() -> None:
    """Demonstrate basic usage of dynamic prompts with tool calling."""

    # Initialize processor with user permissions
    user_permissions = {Permission.StatementsPermission}
    processor = EnhancedFinancialQueryProcessor(
        user_permissions=user_permissions, enable_dynamic_prompts=True
    )

    # Test queries that should benefit from dynamic prompts
    test_queries = [
        "What is the preferred stock additional paid in capital for Apple?",
        "Show me the convertible preferred stock for Tesla",
        "Get the total revenue for Microsoft",
    ]

    for i, query in enumerate(test_queries, 1):
        result = processor.process_query(query)

        if result["success"]:
            pass
        else:
            pass


def demo_static_vs_dynamic_comparison() -> None:
    """Compare static vs dynamic prompt performance."""

    user_permissions = {Permission.StatementsPermission}
    test_query = "What is the preferred stock additional paid in capital for Apple?"

    # Test with static prompts
    static_processor = EnhancedFinancialQueryProcessor(
        user_permissions=user_permissions, enable_dynamic_prompts=False
    )

    static_result = static_processor.process_query(test_query)
    static_tool_calls = static_result["llm_response"].get("tool_calls", [])

    if static_tool_calls:
        static_tool_calls[0].get("parameters", {})

    dynamic_processor = EnhancedFinancialQueryProcessor(
        user_permissions=user_permissions, enable_dynamic_prompts=True
    )

    dynamic_result = dynamic_processor.process_query(test_query)
    dynamic_tool_calls = dynamic_result["llm_response"].get("tool_calls", [])

    if dynamic_tool_calls:
        dynamic_tool_calls[0].get("parameters", {})

    # Compare accuracy

    # Check if dynamic approach used correct parameter
    correct_param = "additional_paid_in_capital_preferred_stock"
    any(correct_param in str(call.get("parameters", {})) for call in dynamic_tool_calls)
    any(correct_param in str(call.get("parameters", {})) for call in static_tool_calls)


def demo_real_world_integration() -> None:
    """Show how this would integrate with real kfinance client."""


if __name__ == "__main__":
    """Run all demonstrations."""
    try:
        demo_basic_usage()
        demo_static_vs_dynamic_comparison()
        demo_real_world_integration()

    except (RuntimeError, ValueError, OSError, ImportError):
        import traceback

        traceback.print_exc()
