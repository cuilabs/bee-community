# Bee by HEOSSI — Public Developer Resources

> Open community repository for **Bee** by [HEOSSI](https://www.heossi.com) — public code, developer tooling, documentation, examples, and community-facing components for building with and contributing to Bee.

[![npm](https://img.shields.io/npm/v/@cuilabs/bee.svg)](https://www.npmjs.com/package/@cuilabs/bee)
[![PyPI](https://img.shields.io/pypi/v/bee-sdk.svg)](https://pypi.org/project/bee-sdk/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)

<!-- mcp-name: io.github.heossihq/bee-public -->

## What's here

| Path | What |
|---|---|
| [`mcp/`](./mcp) | Bee MCP Server install instructions for Claude Desktop, Cursor, VS Code, Zed, Windsurf, OpenCode |
| [`llms-install.md`](./llms-install.md) | AI-agent-readable MCP install guide (Cline & friends) |
| [`sdks/typescript/`](./sdks/typescript) | Pointer + quickstart for `@cuilabs/bee` (live on npm) |
| [`sdks/python/`](./sdks/python) | Pointer + quickstart for `bee-sdk` (live on PyPI) |
| [`examples/typescript/`](./examples/typescript) | Working `@cuilabs/bee` SDK examples (quickstart, streaming, vision) |
| [`examples/python/`](./examples/python) | Working `bee-sdk` examples |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | How to file an issue, propose a change, or run a workshop on Bee |

## SDKs

```bash
# TypeScript / JavaScript / Node / Deno / Bun / browsers — live on npm
npm install @cuilabs/bee

# Python (3.10+) — live on PyPI; also ships the `bee-mcp` MCP server
pip install bee-sdk
```

Full install + quickstart: [bee.heossi.com/docs/sdks](https://bee.heossi.com/docs/sdks).

## MCP Server (Claude Desktop, Cursor, VS Code…)

Bee ships a hosted MCP server with 14 governed tools spanning intelligence,
code, security, research, provenance, usage, documents, memory, and Quantum
Reasoning Lab. It supports stdio and request/response Streamable HTTP. Hosted
calls are authenticated, tenant-scoped, plan/policy gated, and metered by the
Bee gateway.

```bash
pip install bee-sdk          # provides the `bee-mcp` console script
export BEE_API_KEY=bee_sk_…  # create at bee.heossi.com/app/account/api-keys
bee-mcp                      # stdio transport — what every desktop client uses
```

See [mcp/](./mcp) for the exact catalog and per-client configs, or
[bee.heossi.com/docs/mcp](https://bee.heossi.com/docs/mcp).

## Quickstart

```ts
import { BeeClient } from "@cuilabs/bee";

const bee = new BeeClient({ apiKey: process.env.BEE_API_KEY! });

const out = await bee.chat.completions.create({
  model: "bee-cell",
  messages: [{ role: "user", content: "What is Bee?" }],
});

console.log(out.choices[0].message.content);
```

Get an API key at [bee.heossi.com/app/account/api-keys](https://bee.heossi.com/app/account/api-keys).

## What this repo is *not*

- **Not the Bee engine source.** The proprietary engine lives in HEOSSI's private monorepo. This repository contains public SDK pointers, MCP install material, examples, and documentation.
- **Not a release vehicle.** SDKs are released to npm + PyPI. This repo mirrors the source tree of the published packages and links out.
- **Not in scope for product support tickets.** Use [bee.heossi.com/contact](https://bee.heossi.com/contact) for product support; use this repo's issues for SDK, MCP, and example bugs.

## Status

- 🟢 [bee.heossi.com/status](https://bee.heossi.com/status) — live service status
- 📍 [bee.heossi.com/roadmap](https://bee.heossi.com/roadmap) — what's next
- 📰 [bee.heossi.com/changelog](https://bee.heossi.com/changelog) — what shipped

## License

[Apache-2.0](./LICENSE) — © 2026 HEOSSI (Pte.) Ltd.
