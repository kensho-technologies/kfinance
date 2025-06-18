from typing import Literal, Optional

import click
from fastmcp import FastMCP
from fastmcp.tools import FunctionTool
from fastmcp.utilities.logging import get_logger
from langchain_core.utils.function_calling import convert_to_openai_tool

from kfinance.kfinance import Client
from kfinance.tool_calling import KfinanceTool


logger = get_logger(__name__)


def build_mcp_tool_from_kfinance_tool(kfinance_tool: KfinanceTool) -> FunctionTool:
    """Build an MCP FunctionTool from a langchain KfinanceTool."""

    return FunctionTool(
        name=kfinance_tool.name,
        description=kfinance_tool.description,
        # MCP expects a JSON schema for tool params, which we
        # can generate similar to how langchain generates openai json schemas.
        parameters=convert_to_openai_tool(kfinance_tool)["function"]["parameters"],
        # The langchain runner internally validates input arguments via the args_schema.
        # When running with mcp, we need to reproduce that validation ourselves in
        # run_without_langchain (which then calls _run).
        # If we pass in the underlying _run method directly, mcp generates a schema from
        # the _run type hints but bypasses our internal validation. This causes errors,
        # for example with integer literals, which our args models allow but the
        # mcp-internal validation disallows.
        fn=kfinance_tool.run_without_langchain,
    )


@click.command()
@click.option("--stdio/--sse", "-s/ ", default=False)
@click.option("--refresh-token", required=False)
@click.option("--client-id", required=False)
@click.option("--private-key", required=False)
def run_mcp(
    stdio: bool,
    refresh_token: Optional[str] = None,
    client_id: Optional[str] = None,
    private_key: Optional[str] = None,
) -> None:
    """Run the Kfinance MCP server with specified configuration.

    This function initializes and starts an MCP server that exposes Kfinance
    tools. The server supports multiple authentication methods and
    transport protocols to accommodate different deployment scenarios.

    Authentication Methods (in order of precedence):
    1. Refresh Token: Uses an existing refresh token for authentication
    2. Key Pair: Uses client ID and private key for authentication
    3. Browser: Falls back to browser-based authentication flow

    :param stdio: If True, use STDIO transport; if False, use SSE transport.
    :type stdio: bool
    :param refresh_token: OAuth refresh token for authentication
    :type refresh_token: str
    :param client_id: Client id for key-pair authentication
    :type client_id: str
    :param private_key: Private key for key-pair authentication.
    :type private_key: str
    """
    transport: Literal["stdio", "sse"] = "stdio" if stdio else "sse"
    logger.info("Sever will run with %s transport", transport)
    if refresh_token:
        logger.info("The client will be authenticated using a refresh token")
        kfinance_client = Client(refresh_token=refresh_token)
    elif client_id and private_key:
        logger.info("The client will be authenticated using a key pair")
        kfinance_client = Client(client_id=client_id, private_key=private_key)
    else:
        logger.info("The client will be authenticated using a browser")
        kfinance_client = Client()

    kfinance_mcp: FastMCP = FastMCP("Kfinance")
    for langchain_tool in kfinance_client.langchain_tools:
        logger.info("Adding %s to server", langchain_tool.name)
        kfinance_mcp.add_tool(build_mcp_tool_from_kfinance_tool(langchain_tool))

    logger.info("Server starting")
    kfinance_mcp.run(transport=transport)


if __name__ == "__main__":
    run_mcp()
