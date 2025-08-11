from kfinance.integrations.local_mcp.local_mcp import run_mcp


# Before the 3.0.0 update, local mcp could be run from kfinance.mcp.
# With the 3.0.0 update, the local mcp has moved to kfinance.integrations.local_mcp
# However, to avoid requiring users to update their mcp config json with a new path,
# we retain the file here, so that running `python -m kfinance.mcp` still works.
if __name__ == "__main__":
    run_mcp()
