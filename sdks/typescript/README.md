# @cuilabs/bee (TypeScript)

Pointer page for the TypeScript / JavaScript SDK. The package source lives in the main Bee repo at [`sdks/typescript/`](https://github.com/cuilabs/bee/tree/master/sdks/typescript) and ships to npm on every release.

## Install

```bash
npm install @cuilabs/bee
# or pnpm add @cuilabs/bee
# or yarn add @cuilabs/bee
```

[![npm](https://img.shields.io/npm/v/@cuilabs/bee.svg)](https://www.npmjs.com/package/@cuilabs/bee)

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

## More

- Marketing-site install + code samples: [bee.cuilabs.io/docs/sdks](https://bee.cuilabs.io/docs/sdks)
- Working examples (quickstart, streaming, vision): [`examples/typescript/`](../../examples/typescript)
- Source: [github.com/cuilabs/bee/tree/master/sdks/typescript](https://github.com/cuilabs/bee/tree/master/sdks/typescript)
- npm: [npmjs.com/package/@cuilabs/bee](https://www.npmjs.com/package/@cuilabs/bee)
