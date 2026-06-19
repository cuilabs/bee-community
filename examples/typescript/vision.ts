/**
 * Vision example — multimodal content (text + image_url) on Hive / Swarm /
 * Enclave tiers. Lower tiers (Cell / Brood / Comb / Buzz) are text-only;
 * sending image content to them returns a tier-mismatch error.
 *
 * Run:
 *   pnpm add @heossi/bee
 *   BEE_API_KEY=sk-bee-... npx tsx vision.ts
 */

import { BeeClient } from "@heossi/bee";

const bee = new BeeClient({ apiKey: process.env.BEE_API_KEY ?? "" });

const out = await bee.chat.completions.create({
  model: "bee-hive",
  messages: [
    {
      role: "user",
      content: [
        { type: "text", text: "What is happening in this image? One sentence." },
        {
          type: "image_url",
          image_url: {
            url: "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Honey_bee_%28Apis_mellifera%29.jpg/640px-Honey_bee_%28Apis_mellifera%29.jpg",
          },
        },
      ],
    },
  ],
  max_tokens: 120,
});

console.log(out.choices[0].message.content);
