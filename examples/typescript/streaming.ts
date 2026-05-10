/**
 * Streaming Bee chat completion via async iterator.
 *
 * Run:
 *   pnpm add @cuilabs/bee
 *   BEE_API_KEY=sk-bee-... npx tsx streaming.ts
 */

import { BeeClient } from "@cuilabs/bee";

const bee = new BeeClient({ apiKey: process.env.BEE_API_KEY ?? "" });

const stream = await bee.chat.completions.create({
  model: "bee-cell",
  messages: [{ role: "user", content: "Write a short haiku about bees." }],
  stream: true,
});

for await (const chunk of stream) {
  const piece = chunk.choices[0]?.delta?.content;
  if (piece) process.stdout.write(piece);
}
process.stdout.write("\n");
