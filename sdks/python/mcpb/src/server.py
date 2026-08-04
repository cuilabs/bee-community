"""Bee MCP bundle entry point.

The .mcpb host (Claude Desktop) runs this via `uv run`, which resolves the
`bee-sdk` dependency from pyproject.toml and provides BEE_API_KEY from the
user's secure extension config. The actual server lives in bee_sdk.mcp.
"""
from bee_sdk.mcp import main

if __name__ == "__main__":
    main()
