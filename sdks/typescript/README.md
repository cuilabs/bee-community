# @heossi/bee (TypeScript)

Pointer page for the TypeScript / JavaScript SDK. The package is published on npm as [`@heossi/bee`](https://www.npmjs.com/package/@heossi/bee) and ships on every release.

## Install

```bash
npm install @heossi/bee
# or pnpm add @heossi/bee
# or yarn add @heossi/bee
```

[![npm](https://img.shields.io/npm/v/@heossi/bee.svg)](https://www.npmjs.com/package/@heossi/bee)

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

## More

- Marketing-site install + code samples: [bee.heossi.com/docs/sdks](https://bee.heossi.com/docs/sdks)
- Working examples (quickstart, streaming, vision): [`examples/typescript/`](../../examples/typescript)
- npm: [npmjs.com/package/@heossi/bee](https://www.npmjs.com/package/@heossi/bee)
