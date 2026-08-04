# Bee MCP server

Bee MCP exposes fourteen governed tools through the hosted Bee gateway. Calls are authenticated, tenant-scoped, plan-gated, and metered. The server uses stdio locally and forwards requests to Bee over HTTPS.

## Run

```bash
export BEE_API_KEY=bee_sk_…
uvx --from bee-sdk@latest bee-mcp
```

Create a key at [Bee Workspace](https://workspace.bee.heossi.com/account/api-keys). The canonical registry identity is `io.github.heossihq/bee-public`.

## Client configuration

Use this command in Claude Desktop, Cursor, VS Code, Zed, Windsurf, OpenCode, or any MCP client that supports stdio:

```json
{
  "command": "uvx",
  "args": ["--from", "bee-sdk@latest", "bee-mcp"],
  "env": { "BEE_API_KEY": "${input:beeApiKey}" }
}
```

Never commit a real API key. Client-specific details and the live tool catalog are documented at [bee.heossi.com/docs/mcp](https://bee.heossi.com/docs/mcp).
