# Bee Community

> Open community repository for **Bee** by [CUI Labs](https://www.cuilabs.io) — public code, developer tooling, documentation, examples, and community-facing components for building with and contributing to Bee.

[![npm](https://img.shields.io/npm/v/@cuilabs/bee.svg)](https://www.npmjs.com/package/@cuilabs/bee)
[![PyPI](https://img.shields.io/pypi/v/bee-sdk.svg)](https://pypi.org/project/bee-sdk/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)

## What's here

| Path | What |
|---|---|
| [`mcp/`](./mcp) | Bee MCP Server install instructions for Claude Desktop, Cursor, VS Code, Zed, Windsurf |
| [`sdks/typescript/`](./sdks/typescript) | Pointer + quickstart for `@cuilabs/bee` (live on npm) |
| [`sdks/python/`](./sdks/python) | Pointer + quickstart for `bee-sdk` (PyPI org pending — install from GitHub for now) |
| [`examples/typescript/`](./examples/typescript) | Working `@cuilabs/bee` SDK examples (quickstart, streaming, vision) |
| [`examples/python/`](./examples/python) | Working `bee-sdk` examples |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | How to file an issue, propose a change, or run a workshop on Bee |

## SDKs

```bash
# TypeScript / JavaScript / Node / Deno / Bun / browsers — live on npm
npm install @cuilabs/bee

# Python (3.10+) — install from GitHub while the PyPI `cuilabs` org
# approval is pending; pip install bee-sdk will resolve once it lands.
pip install "git+https://github.com/cuilabs/bee.git#subdirectory=sdks/python"
```

Full install + quickstart on the marketing site: [bee.cuilabs.io/docs/sdks](https://bee.cuilabs.io/docs/sdks).

## MCP Server (Claude Desktop, Cursor, VS Code…)

Bee ships an MCP server that exposes 11 domain-specialised tools (chat, code explanation, security audit, threat modelling, quantum circuits, smart-contract review, paper critique, …) over the Model Context Protocol.

See [mcp/](./mcp) for per-client configs, or the marketing page at [bee.cuilabs.io/docs/mcp](https://bee.cuilabs.io/docs/mcp).

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

Get an API key at [bee.cuilabs.io/app/account/api-keys](https://bee.cuilabs.io/app/account/api-keys).

## What this repo is *not*

- **Not the Bee engine source.** The proprietary engine lives in a private CUI Labs repo. This community repo holds only what's safe to publish: SDKs, MCP install material, examples, and docs.
- **Not a release vehicle.** SDKs are released to npm + PyPI. This repo mirrors the source tree of the published packages and links out.
- **Not in-scope for support tickets.** Use [bee.cuilabs.io/contact](https://bee.cuilabs.io/contact) for product support; use this repo's issues only for SDK / MCP / example bugs.

## Status

- 🟢 [bee.cuilabs.io/status](https://bee.cuilabs.io/status) — live engine status
- 📍 [bee.cuilabs.io/roadmap](https://bee.cuilabs.io/roadmap) — what's next
- 📰 [bee.cuilabs.io/changelog](https://bee.cuilabs.io/changelog) — what shipped

## License

[Apache-2.0](./LICENSE) — © CUI Labs Pte. Ltd.
