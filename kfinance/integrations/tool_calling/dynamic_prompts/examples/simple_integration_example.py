"""Simple example showing the core integration pattern for dynamic prompts with tool calling."""

from typing import Any, Dict, List, Set

from kfinance.client.permission_models import Permission
from kfinance.integrations.tool_calling.dynamic_prompts import construct_dynamic_prompt


def simple_tool_calling_with_dynamic_prompts(
    query: str,
    user_permissions: Set[Permission],
    llm_client: Any,  # Your LLM client (OpenAI, Anthropic, etc.)
    available_tools: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Simple integration pattern for using dynamic prompts with tool calling.

    This is the core pattern you would use in your kfinance client.
    """

    # Step 1: Construct dynamic prompt with relevant examples
    dynamic_prompt = construct_dynamic_prompt(
        query=query,
        user_permissions=user_permissions,
    )

    # Step 2: Send prompt to LLM with available tools
    llm_response = llm_client.generate_with_tools(
        prompt=dynamic_prompt,
        tools=available_tools,
    )

    # Step 3: Execute any tool calls returned by the LLM
    results = []
    for tool_call in llm_response.get("tool_calls", []):
        # Execute the tool (replace with your actual tool execution)
        tool_result = execute_kfinance_tool(
            tool_call["name"],
            tool_call["parameters"]
        )
        results.append(tool_result)

    return {
        "query": query,
        "llm_response": llm_response,
        "tool_results": results,
    }


def execute_kfinance_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a kfinance tool - replace with your actual implementation."""
    # This is where you would call your actual kfinance tools
    # from kfinance.integrations.tool_calling.all_tools import ALL_TOOLS

    # Find and execute the tool
    # for tool_class in ALL_TOOLS:
    #     if tool_class.name == tool_name:
    #         tool_instance = tool_class()
    #         return tool_instance.execute(parameters)

    # Mock implementation for demo
    return {
        "success": True,
        "data": f"Executed {tool_name} with {parameters}",
    }


# Example usage:
if __name__ == "__main__":
    # Your query
    query = "What is the preferred stock additional paid in capital for Apple?"

    # User permissions
    user_permissions = {Permission.StatementsPermission}

    # Available tools (simplified)
    available_tools = [
        {
            "name": "get_financial_line_item_from_identifiers",
            "description": "Get financial line items for companies",
            "parameters": {
                "type": "object",
                "properties": {
                    "identifiers": {"type": "array", "items": {"type": "string"}},
                    "line_item": {"type": "string"},
                },
                "required": ["identifiers", "line_item"]
            }
        }
    ]

    # Mock LLM client (replace with your actual client)
    class MockLLMClient:
        """Mock LLM client for demonstration purposes."""
        
        def generate_with_tools(self, prompt: str, tools: List[Dict]) -> Dict:
            # Your LLM would analyze the prompt and return tool calls
            return {
                "tool_calls": [{
                    "name": "get_financial_line_item_from_identifiers",
                    "parameters": {
                        "identifiers": ["AAPL"],
                        "line_item": "additional_paid_in_capital_preferred_stock"
                    }
                }],
                "reasoning": "Based on the examples, using correct parameter name."
            }

    # Process the query
    result = simple_tool_calling_with_dynamic_prompts(
        query=query,
        user_permissions=user_permissions,
        llm_client=MockLLMClient(),
        available_tools=available_tools,
    )

