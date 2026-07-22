# Bee MCP Server

Connect **Bee by HEOSSI — The Progressive Quantum-Native Intelligence
Engine** to Claude Desktop, Claude Code, Cursor, VS Code, Zed, Windsurf,
OpenCode, or another Model Context Protocol client.

The installable server is published in
[`bee-sdk`](https://pypi.org/project/bee-sdk/). It is a thin client: no model
weights or GPU run on the user's machine. Hosted tool calls go through the Bee
gateway, where API-key authentication, tenant isolation, plan and policy gates,
allowances, and usage metering are enforced.

| Transport | Status |
|---|---|
| stdio | Supported; default for desktop and IDE clients |
| Streamable HTTP | Supported with `bee-mcp --http PORT`; binds to localhost by default |

## Exact catalog (14 tools)

| Tool | Behavior |
|---|---|
| `bee_chat` | General or domain-specialist generated response |
| `bee_code` | Explain, fix, refactor, or propose tests; never edits files or runs commands |
| `bee_security` | Defensive audit, threat model, authorized pentest support, or contract review |
| `bee_research` | NISQ-honest circuit design or research-paper critique |
| `bee_verify_provenance` | Read-only verification of an ML-DSA-65 sealed coding session |
| `bee_usage` | Read-only plan, allowance, reset, and recent-usage view |
| `bee_documents_search` | Read-only tenant document retrieval; RAG entitlement required |
| `bee_documents_add` | Persists supplied text to the tenant's hosted knowledge base |
| `bee_memory_search` | Read-only recall governed by memory setting and tenant policy |
| `bee_memory_add` | Persists an intended user fact; near-duplicates are suppressed |
| `bee_quantum_reasoning_run` | Creates a metered, durable Lab job on an eligible hosted product |
| `bee_quantum_reasoning_jobs` | Lists tenant-scoped retained Lab jobs and capabilities |
| `bee_quantum_reasoning_get` | Reads status, result, evidence, usage, and receipt for one Lab job |
| `bee_quantum_reasoning_remove` | Destructively cancels or erases an eligible Lab job |

Ten tools are read-only and four are explicit writes. Every tool publishes MCP
`readOnlyHint`, `destructiveHint`, `idempotentHint`, and `openWorldHint`
annotations.

Resources: `bee://status`, `bee://domains`, `bee://documents`, and
`bee://memory`. The `bee://documents/{source}` resource template reconstructs
one tenant document.

## Install

```bash
pip install bee-sdk
export BEE_API_KEY=bee_sk_...  # create at https://bee.heossi.com/app/account/api-keys
bee-mcp --help
```

No-install alternative:

```bash
uvx --from "bee-sdk@latest" bee-mcp
```

Use the JSON in [`configs/`](./configs) for Claude Desktop, Cursor, VS Code,
Zed, Windsurf, or OpenCode. Replace `bee_sk_...` with the caller's own key.
Never place a key in source control.

For remote/self-hosted transport:

```bash
bee-mcp --http 8765
```

The HTTP server binds to `127.0.0.1` by default. Set
`BEE_MCP_HTTP_HOST=0.0.0.0` only behind a trusted authenticated proxy. An
inbound `Authorization: Bearer bee_sk_...` header selects the tenant-scoped
caller for that request.

## Container and Glama inspection

The root [`Dockerfile`](../Dockerfile) pins the currently published SDK and
starts the stdio server. MCP initialization and catalog inspection require no
API key and incur no Bee inference cost. Actual hosted tool calls require a
valid caller key and remain metered.

Glama maintainer metadata is declared in [`glama.json`](../glama.json). The
quality badge will be added only after Glama has built, inspected, and scored
this repository; the repository does not display a speculative badge.

## Verification

An MCP client should observe server name `bee`, 14 tools, four resources, and
one resource template. Write tools are clearly annotated. A missing key must
produce an honest authentication error on tool invocation rather than during
catalog inspection.

Documentation: [bee.heossi.com/docs/mcp](https://bee.heossi.com/docs/mcp)

Issues: [heossihq/bee-public/issues](https://github.com/heossihq/bee-public/issues)

## License

[Apache-2.0](../LICENSE) — © 2026 HEOSSI (Pte.) Ltd.
