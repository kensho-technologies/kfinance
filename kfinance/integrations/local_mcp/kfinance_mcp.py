from fastmcp import FastMCP


class KfinanceMcp(FastMCP):
    """FastMCP subclass with some kfinance specific adaptations."""

    def _setup_handlers(self) -> None:
        """Skip low level input validation for tool calls.

        We do validate inputs as part of KfinanceTool.run_without_langchain.
        However, the mcp python sdk recently added its own low-level validation:
        github.com/modelcontextprotocol/python-sdk/commit/c8bbfc034d5cb876d6b91185cf02da2af6fb8b44
        This causes problems because claude always returns integer values as strings if
        they are part of a field that allows multiple types. e.g. `start_year: int | None`
        -> Claude will always return strings. This is fine for pydantic, it automatically
        converts the strings to integers.
        However, the mcp sdk validation is stricter and disallows strings where ints are
        required.
        call_tool(validate_input=False) turns off the mcp sdk validation.
        """
        super()._setup_handlers()
        self._mcp_server.call_tool(validate_input=False)(self._mcp_call_tool)
