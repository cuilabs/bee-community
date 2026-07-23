/**
 * Minimal Bee SDK quickstart — chat completion with no streaming.
 *
 * Run:
 *   pnpm add @heossi/bee
 *   BEE_API_KEY=sk-bee-... npx tsx quickstart.ts
 */

import { BeeClient } from "@heossi/bee";

const apiKey = process.env.BEE_API_KEY;
if (!apiKey) {
  console.error(
    "Set BEE_API_KEY first — issue one at https://workspace.bee.heossi.com/account/api-keys",
  );
  process.exit(1);
}

const bee = new BeeClient({ apiKey });

const out = await bee.chat.completions.create({
  model: "bee-cell",
  messages: [
    { role: "system", content: "You are a precise assistant." },
    { role: "user", content: "Summarise the SOLID principles in 2 lines." },
  ],
  temperature: 0.4,
});

console.log(out.choices[0].message.content);
console.log(`\n[tokens prompt=${out.usage.prompt_tokens} completion=${out.usage.completion_tokens}]`);
