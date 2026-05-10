# Bee MCP Server

Connect Bee to **Claude Desktop**, **Claude Code**, **Cursor**, **VS Code**, **Zed**, or **Windsurf** via the [Model Context Protocol](https://modelcontextprotocol.io) — Anthropic's open standard for LLM ↔ tool integration.

| Transport | Status |
|---|---|
| stdio | ✅ supported (every desktop MCP client uses this) |
| HTTP | 🚧 coming soon (`--http <port>` is a stub today; see [bee.cuilabs.io/roadmap](https://bee.cuilabs.io/roadmap) Stage 3) |

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

Resources: `bee://status` (active domain + loaded adapter inventory), `bee://domains` (full domain list).

## Install

```bash
# 1. Clone Bee + install the Python package (engine + MCP server live together)
git clone https://github.com/cuilabs/bee
cd bee
pip install -e .

# 2. Verify the MCP server runs
python -m bee.mcp_server --help
```

## Wire your client

Pick one config from [`configs/`](./configs):

- [`configs/claude-desktop.json`](./configs/claude-desktop.json) — Claude Desktop
- [`configs/cursor.json`](./configs/cursor.json) — Cursor / Windsurf / Zed (project-local mcp config)
- [`configs/vscode.json`](./configs/vscode.json) — VS Code (Continue, Cline, MCP extension)

Each file is the literal JSON snippet to drop into the corresponding client's MCP config location.

## Honest fallback

If a domain LoRA adapter isn't present locally, the tool still answers from the base model — without domain specialisation. We don't pretend the adapter is there. The tool's response includes a header noting which adapter served the answer.

## Where things live

- **Source:** [github.com/cuilabs/bee/blob/master/bee/mcp_server.py](https://github.com/cuilabs/bee/blob/master/bee/mcp_server.py) (688 LoC, Python)
- **Docs:** [bee.cuilabs.io/docs/mcp](https://bee.cuilabs.io/docs/mcp)
- **Spec:** [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Issues with the MCP server:** open an issue on this repo

## License

[Apache-2.0](../LICENSE)
