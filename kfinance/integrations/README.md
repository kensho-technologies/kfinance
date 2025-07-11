# Integrations

Integrations holds integrations downstream from the main
Kfinance `Client`. This currently includes tool calling
and MCP. Note that only shared functionality for tool 
calling should be put into the `tool_calling` directory.
The tools themselves should be defined in the relevant
`domains` sub directory.