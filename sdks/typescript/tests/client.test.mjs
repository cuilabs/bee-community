import assert from "node:assert/strict";
import test from "node:test";

import { BeeActionRequiredError, BeeClient } from "../dist/index.js";

test("chat completions use the canonical public API route", async () => {
  const calls = [];
  const expected = {
    id: "chatcmpl-test",
    object: "chat.completion",
    created: 0,
    model: "bee-cell",
    choices: [{ index: 0, message: { role: "assistant", content: "hello" }, finish_reason: "stop" }],
    usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 },
  };
  const client = new BeeClient({
    apiKey: "test-api-key-not-a-secret",
    fetch: async (url, init) => {
      calls.push({ url, init });
      return new Response(JSON.stringify(expected), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    },
  });

  const result = await client.chat.completions.create({
    model: "bee-cell",
    domain: "cryptography_pqc",
    messages: [{ role: "user", content: "hello" }],
  });

  assert.deepEqual(result, expected);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "https://api.bee.heossi.com/bee/chat/completions");
  assert.equal(calls[0].init.method, "POST");
  assert.equal(JSON.parse(calls[0].init.body).domain, "cryptography_pqc");
});

test("structured upgrade decisions become typed action errors", async () => {
  const decision = {
    schema_version: "2026-07-31",
    reason: "model_access_required",
    current_plan: "api-free",
    required_plan: "api-build",
    requested_model: "bee-hive",
    actions: [
      {
        kind: "upgrade_plan",
        label: "Upgrade to api-build",
        available: true,
        url: "https://workspace.bee.heossi.com/account/billing",
        plan_id: "api-build",
      },
    ],
  };
  const client = new BeeClient({
    apiKey: "test-api-key-not-a-secret",
    fetch: async () =>
      new Response(
        JSON.stringify({
          error: "model_access_denied",
          message: "Upgrade required.",
          bee_upgrade: decision,
        }),
        { status: 403, headers: { "content-type": "application/json" } },
      ),
  });

  await assert.rejects(
    () =>
      client.chat.completions.create({
        model: "bee-hive",
        messages: [{ role: "user", content: "hello" }],
      }),
    (error) => {
      assert.ok(error instanceof BeeActionRequiredError);
      assert.deepEqual(error.decision, decision);
      return true;
    },
  );
});
