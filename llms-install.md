# Bee MCP Server — AI-agent install guide

This guide is written for AI agents (Cline, Claude, Cursor agents, …) installing
the Bee MCP server on a user's machine. Follow the steps in order. Every step is
verifiable; do not skip the verification commands.

## What you are installing

`bee-mcp` — an MCP server exposing 14 governed intelligence, code, security,
research, provenance, usage, document, memory, and Quantum Reasoning Lab tools.
It is a thin client: tool calls are forwarded to the hosted Bee gateway
(`https://api.bee.heossi.com/bee`),
so it needs no GPU and no model download. It ships inside the `bee-sdk` PyPI
package with zero extra dependencies.

## Prerequisites

- Python 3.10+ (`python3 --version`)
- A Bee API key (`bee_sk_...`). If the user does not have one, direct them to
  create it at https://workspace.bee.heossi.com/account/api-keys — the free Cell tier
  works. Do NOT proceed without a key; tool calls return 401 without it.

## Step 1 — Install

```bash
pip install bee-sdk
```

Alternative without a persistent install (preferred if `uv` is available):
use `uvx --from "bee-sdk@latest" bee-mcp` as the command in Step 3 and skip pip entirely.

## Step 2 — Verify the server starts

```bash
bee-mcp --help
```

Expected: usage text mentioning "Bee MCP Server". If `bee-mcp` is not on PATH,
use `python3 -m bee_sdk.mcp` as the command instead.

## Step 3 — Register the server in the MCP client config

Add this JSON to the client's MCP configuration (e.g. `cline_mcp_settings.json`,
`claude_desktop_config.json`, or `.cursor/mcp.json`), substituting the user's
real API key:

```json
{
  "mcpServers": {
    "bee": {
      "command": "uvx",
      "args": ["--from", "bee-sdk@latest", "bee-mcp"],
      "env": { "BEE_API_KEY": "bee_sk_..." }
    }
  }
}
```

If `uvx` is unavailable, use `"command": "bee-mcp", "args": []` (requires Step 1's
pip install).

## Step 4 — Verify end-to-end

After the client restarts/reloads MCP servers, confirm:

1. The server "bee" connects and lists **14 tools**. The exact names are in
   [`mcp/README.md`](./mcp/README.md). It also lists **4 resources**:
   `bee://status`, `bee://domains`, `bee://documents`, and `bee://memory`.
2. Call `bee_chat` with `{"message": "Say OK.", "max_tokens": 16}`. A non-empty
   text response proves the gateway path works. The first call may take up to
   ~2 minutes if the serverless backend is cold — this is normal; do not retry
   in a tight loop.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Tool calls return "Bee API error (401)" | `BEE_API_KEY` missing/invalid — create one at https://workspace.bee.heossi.com/account/api-keys |
| `bee-mcp: command not found` | Use `python3 -m bee_sdk.mcp`, or ensure pip's bin dir is on PATH |
| First tool call is slow (~1–2 min) | Serverless cold start — expected, subsequent calls are fast |
| Remote HTTP does not bind publicly | It binds to localhost by default; set `BEE_MCP_HTTP_HOST=0.0.0.0` only behind a trusted authenticated proxy |

## Links

- Docs: https://bee.heossi.com/docs/mcp
- Package: https://pypi.org/project/bee-sdk/
- Registry metadata name: `io.github.heossihq/bee-public`
