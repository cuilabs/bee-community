# Bee MCP Server

Connect Bee to **Claude Desktop**, **Claude Code**, **Cursor**, **VS Code**, **Zed**, **Windsurf**, or **OpenCode** via the [Model Context Protocol](https://modelcontextprotocol.io) — Anthropic's open standard for LLM ↔ tool integration.

Listed on the [official MCP Registry](https://registry.modelcontextprotocol.io) as **`io.github.cuilabs/bee`**.

| Transport | Status |
|---|---|
| stdio | ✅ supported (every desktop MCP client uses this) |
| HTTP | 🚧 coming soon (`--http <port>` exits with a clear error today; see [bee.cuilabs.io/roadmap](https://bee.cuilabs.io/roadmap)) |

## Tools exposed (11)

| Tool | Purpose | Domain adapter |
|---|---|---|
| `bee_chat` | General Q&A with explicit domain selector | any of 10 |
| `bee_explain_code` | Walk through what a snippet does | programming |
| `bee_fix_code` | Suggest a fix for a bug or failing test | programming |
| `bee_refactor` | Restructure code without changing behaviour | programming |
| `bee_write_tests` | Propose unit / integration tests | programming |
| `bee_security_audit` | Scan code for vulnerabilities | cybersecurity |
| `bee_threat_model` | STRIDE / PASTA / LINDDUN threat model | cybersecurity |
| `bee_pentest_assist` | Offensive security guidance — explicit-authorisation context required | cybersecurity |
| `bee_quantum_circuit` | NISQ-aware Qiskit circuit design | quantum |
| `bee_smart_contract_review` | Smart-contract audit (SWC-Registry framing) | blockchain |
| `bee_paper_critique` | Literature review / methodology critique | research |

Resources: `bee://status` (gateway connectivity + auth status), `bee://domains` (full domain list).

## Install (hosted — recommended)

The server ships inside the [`bee-sdk`](https://pypi.org/project/bee-sdk/) Python package (zero extra dependencies) and forwards every tool call to the hosted Bee gateway — no GPU, no model download, no engine checkout.

```bash
# 1. Install (Python 3.10+)
pip install bee-sdk

# 2. Get an API key (the free Cell tier works)
#    -> https://bee.cuilabs.io/app/account/api-keys
export BEE_API_KEY=bee_sk_...

# 3. Verify it runs
bee-mcp --help
```

No-install alternative (used by the configs below): `uvx --from "bee-sdk@latest" bee-mcp`.

## Wire your client

Pick one config from [`configs/`](./configs):

- [`configs/claude-desktop.json`](./configs/claude-desktop.json) — Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS)
- [`configs/cursor.json`](./configs/cursor.json) — Cursor / Windsurf / Zed (project-local mcp config)
- [`configs/vscode.json`](./configs/vscode.json) — VS Code (Copilot agent mode, Continue, Cline)
- [`configs/opencode.json`](./configs/opencode.json) — OpenCode (`~/.config/opencode/opencode.json`)

Each file is the literal JSON snippet to drop into the corresponding client's MCP config location. Replace `bee_sk_...` with your key.

One-click install for Cursor, and the `code --add-mcp` command for VS Code, live on the docs page: [bee.cuilabs.io/docs/mcp](https://bee.cuilabs.io/docs/mcp).

> **AI agents (Cline, etc.):** see [`../llms-install.md`](../llms-install.md) for a step-by-step machine-readable install guide.

## Honest fallback

If a domain LoRA adapter isn't promoted for a domain yet, the tool still answers from the base model — without domain specialisation. We don't pretend the adapter is there.

## Advanced: local-model server

Core contributors with access to the private `cuilabs/bee` engine repo can run the local-model variant (`python -m bee.mcp_server`), which loads weights + adapters on their own hardware (GPU/MPS) instead of calling the hosted gateway. It exposes the identical 11 tools. That path requires the private repo and is **not** available to the public — the hosted `bee-mcp` above is the supported public path.

## Where things live

- **Server package:** [pypi.org/project/bee-sdk](https://pypi.org/project/bee-sdk/) (`bee_sdk/mcp.py`)
- **Registry entry:** [`io.github.cuilabs/bee`](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.cuilabs/bee)
- **Docs:** [bee.cuilabs.io/docs/mcp](https://bee.cuilabs.io/docs/mcp)
- **Spec:** [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Issues with the MCP server:** open an issue on this repo

## License

[Apache-2.0](../LICENSE)
