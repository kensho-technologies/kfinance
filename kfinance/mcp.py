from textwrap import dedent
from typing import Literal, Optional

import click
from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger

from kfinance.kfinance import Client
from kfinance.tool_calling.shared_models import KfinanceTool


logger = get_logger(__name__)


def build_doc_string(tool: KfinanceTool) -> str:
    """Build a formatted documentation string for a Kfinance tool.

    This function takes a KfinanceTool object and constructs a comprehensive
    documentation string that includes the tool's description and detailed
    information about its arguments, including default values and descriptions.

    :param tool: The Kfinance tool object containing metadata about the tool's functionality, description, and argument schema.
    :type tool: KfinanceTool
    :return: A formatted documentation string containing for the tool description with detailed argument information.
    :rtype: str
    """

    description = dedent(f"""
        {tool.description}

        Args:
    """).strip()

    for arg_name, arg_field in tool.args_schema.model_fields.items():
        default_value_description = (
            f"Default: {arg_field.default}. " if not arg_field.is_required() else ""
        )
        param_description = f"\n    {arg_name}: {default_value_description}{arg_field.description}"
        description += param_description

    return description


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
    for tool in kfinance_client.langchain_tools:
        logger.info("Adding %s to server", tool.name)
        kfinance_mcp.tool(
            name_or_fn=getattr(tool, "_run"),
            name=tool.name,
            description=build_doc_string(tool),
        )

    logger.info("Server starting")
    kfinance_mcp.run(transport=transport)


if __name__ == "__main__":
    run_mcp()
