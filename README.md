# kFinance

The kFinance Python library provides a simple interface for the LLM-ready API, streamlining API requests and response handling. It can be used on its own, with LLMs, or integrated into applications.

For a complete overview of the functions, usage, and features of the kFinance Python library, please refer to documentation [here](https://kensho-kfinance.readthedocs.io/en/stable/).

Any questions or suggestions can be sent to the [kFinance Maintainers](kfinance-maintainers@kensho.com).

# Setup

You can install kFinance on [PyPI](https://pypi.org/project/kensho-kfinance/) via

`pip install kensho-kfinance`

# Getting started

To receive access, please email [S&P Global Market Intelligence](market.intelligence@spglobal.com) for information on free trials and pricing.

Once access is obtained, get started using the [Authentication Guide](https://docs.kensho.com/llmreadyapi/kf-authentication) and [Usage Guide](https://docs.kensho.com/llmreadyapi/usage).

To get started, we provide some notebooks:

- The [LLM-ready API Basic Usage](example_notebooks%2Fbasic_usage.ipynb) notebook demonstrates how
fetch data with the kFinance client.
- The [tool_calling notebooks](example_notebooks%2Ftool_calling) show how the kFinance library can
be used for tool calling. We provide notebooks for OpenAI (GPT), Anthropic (Claude), and Google
  (Gemini). Each of these integrations comes in a langchain version, which uses langchain as a
wrapper to simplify the integration, and as a lower level non-langchain version.

We also provide an [interactive notebook](example_notebooks/basic_usage.ipynb) that demonstrates some usage examples.

# MCP (Model Context Protocol)

To run the kFinance MCP server use:

`python -m kfinance.mcp`

This function initializes and starts an MCP server that exposes the kFinance tools. The server supports multiple authentication methods and transport protocols to accommodate different deployment scenarios.

The server's full signature is as follows:

`kfinance.mcp [--stdio,-s]/[--sse, ] --refresh-token <refresh-token> --client-id <client-id> --private-key <private-key>`

Authentication Methods (in order of precedence):
1. Refresh Token: Uses an existing refresh token for authentication. The `--refresh-token <refresh-token>` argument must be provided.
2. Key Pair: Uses client ID and private key for authentication. Both the `--client-id <client-id>` and `--private-key <private-key>` arguments must be provided.
3. Browser: Falls back to browser-based authentication flow. This occurs if no auth arguments are provided.

Transport Layers:
- stdio can be set by passing either `--stdio` or `-s`
- sse can be set by passing `--sse` or no other transport related flag

# Versioning
The kFinance uses semantic versioning (major, minor, patch).
To bump the version, add a new entry in [CHANGELOG.md](kfinance%2FCHANGELOG.md).
This will generate a new version of the library as part of the release process.

# License

Use is solely in accordance with the signed agreement between your entity and S&P.

Copyright 2025-present Kensho Technologies, LLC. The present date is determined by the timestamp of the most recent commit in the repository.
