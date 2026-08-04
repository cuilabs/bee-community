import { BeeClient } from "@heossihq/bee";

const bee = new BeeClient({ apiKey: process.env.BEE_API_KEY! });
const result = await bee.chat.completions.create({
  model: "bee-cell",
  messages: [{ role: "user", content: "What is Bee?" }],
});

console.log(result.choices[0].message.content);
