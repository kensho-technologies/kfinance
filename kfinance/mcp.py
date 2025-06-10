from textwrap import dedent
from typing import Optional

import click
from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger
from kfinance.kfinance import Client
from kfinance.tool_calling.shared_models import KfinanceTool


logger = get_logger(__name__)

def build_doc_string(tool: KfinanceTool) -> str:

    description = dedent(f"""
        {tool.description}

        Args:
    """).strip()

    for arg_name, arg_field in tool.args_schema.model_fields.items():
        default_value_description = f"Default: {arg_field.default}. " if not arg_field.is_required() else ""
        param_description = f"\n    {arg_name}: {default_value_description}{arg_field.description}"
        description += param_description

    return description

@click.command()
@click.option("--stdio/--sse", "-s/ ", default=False)
@click.option("--refresh-token", required=False)
@click.option("--client-id", required=False)
@click.option("--private-key", required=False)
def run_mcp(stdio: bool, refresh_token: Optional[str] = None , client_id: Optional[str] = None, private_key: Optional[str] = None):
    transport = "stdio" if stdio else "sse"
    logger.info(f"Sever will run with {transport} transport")
    if refresh_token:
        logger.info("The client will be authenticated using a refresh token")
        kfinance_client = Client(refresh_token=refresh_token)
    elif client_id and private_key:
        logger.info("The client will be authenticated using a key pair")
        kfinance_client = Client(client_id=client_id, private_key=private_key)
    else:
        logger.info("The client will be authenticated using a browser")
        kfinance_client = Client()

    kfinance_mcp = FastMCP("Kfinance")
    for tool in kfinance_client.langchain_tools:
        logger.info(f"Adding {tool.name} to server")
        kfinance_mcp.tool(
            name_or_fn=tool._run,
            name=tool.name,
            description=build_doc_string(tool)
        )

    logger.info("Server starting")
    kfinance_mcp.run(transport=transport)


if __name__ == "__main__":
    run_mcp()
