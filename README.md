# Bee Community

> Open community repository for **Bee** by [CUI Labs](https://www.heossi.com) — public code, developer tooling, documentation, examples, and community-facing components for building with and contributing to Bee.

[![npm](https://img.shields.io/npm/v/@heossi/bee.svg)](https://www.npmjs.com/package/@heossi/bee)
[![PyPI](https://img.shields.io/pypi/v/bee-sdk.svg)](https://pypi.org/project/bee-sdk/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)

<!-- mcp-name: io.github.cuilabs/bee -->

## What's here

| Path | What |
|---|---|
| [`mcp/`](./mcp) | Bee MCP Server install instructions for Claude Desktop, Cursor, VS Code, Zed, Windsurf, OpenCode |
| [`llms-install.md`](./llms-install.md) | AI-agent-readable MCP install guide (Cline & friends) |
| [`sdks/typescript/`](./sdks/typescript) | Pointer + quickstart for `@heossi/bee` (live on npm) |
| [`sdks/python/`](./sdks/python) | Pointer + quickstart for `bee-sdk` (live on PyPI) |
| [`examples/typescript/`](./examples/typescript) | Working `@heossi/bee` SDK examples (quickstart, streaming, vision) |
| [`examples/python/`](./examples/python) | Working `bee-sdk` examples |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | How to file an issue, propose a change, or run a workshop on Bee |

## SDKs

```bash
# TypeScript / JavaScript / Node / Deno / Bun / browsers — live on npm
npm install @heossi/bee

# Python (3.10+) — live on PyPI; also ships the `bee-mcp` MCP server
pip install bee-sdk
```

Full install + quickstart on the marketing site: [bee.heossi.com/docs/sdks](https://bee.heossi.com/docs/sdks).

## MCP Server (Claude Desktop, Cursor, VS Code…)

Bee ships an MCP server that exposes 8 tools — `bee_chat` (domain-selectable Q&A), `bee_code` (explain/fix/refactor/test), `bee_security` (audit/threat-model/authorised-pentest), `bee_research` (quantum-circuit/paper-critique), plus documents RAG (`bee_documents_search`/`add`) and personal memory (`bee_memory_search`/`add`) — over the Model Context Protocol. Listed on the [official MCP Registry](https://registry.modelcontextprotocol.io) as `io.github.cuilabs/bee`.

```bash
pip install bee-sdk          # provides the `bee-mcp` console script
export BEE_API_KEY=bee_sk_…  # create at bee.heossi.com/app/account/api-keys
bee-mcp                      # stdio transport — what every desktop client uses
```

See [mcp/](./mcp) for per-client configs, or the marketing page at [bee.heossi.com/docs/mcp](https://bee.heossi.com/docs/mcp).

## Quickstart

```ts
import { BeeClient } from "@heossi/bee";

const bee = new BeeClient({ apiKey: process.env.BEE_API_KEY! });

const out = await bee.chat.completions.create({
  model: "bee-cell",
  messages: [{ role: "user", content: "What is Bee?" }],
});

console.log(out.choices[0].message.content);
```

Get an API key at [bee.heossi.com/app/account/api-keys](https://bee.heossi.com/app/account/api-keys).

## What this repo is *not*

- **Not the Bee engine source.** The proprietary engine lives in a private CUI Labs repo. This community repo holds only what's safe to publish: SDKs, MCP install material, examples, and docs.
- **Not a release vehicle.** SDKs are released to npm + PyPI. This repo mirrors the source tree of the published packages and links out.
- **Not in-scope for support tickets.** Use [bee.heossi.com/contact](https://bee.heossi.com/contact) for product support; use this repo's issues only for SDK / MCP / example bugs.

## Status

- 🟢 [bee.heossi.com/status](https://bee.heossi.com/status) — live engine status
- 📍 [bee.heossi.com/roadmap](https://bee.heossi.com/roadmap) — what's next
- 📰 [bee.heossi.com/changelog](https://bee.heossi.com/changelog) — what shipped

## License

[Apache-2.0](./LICENSE) — © CUI Labs Pte. Ltd.
