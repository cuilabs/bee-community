import assert from "node:assert/strict";
import test from "node:test";

import {
  BeeActionRequiredError,
  BeeAuthError,
  BeeClient,
  BeeError,
  BeeRateLimitError,
  BeeTimeoutError,
} from "../dist/index.js";

const apiKey = "test-api-key-not-a-secret";

function jsonResponse(body, init = {}) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "content-type": "application/json", ...(init.headers ?? {}) },
    ...init,
  });
}

function clientWith(fetch, options = {}) {
  return new BeeClient({ apiKey, fetch, ...options });
}

function recordingClient(responses, options = {}) {
  const calls = [];
  const queue = [...responses];
  const client = clientWith(async (url, init) => {
    calls.push({ url, init });
    assert.ok(queue.length > 0, `unexpected request to ${url}`);
    return queue.shift();
  }, options);
  return { client, calls };
}

const completedJob = Object.freeze({ id: "job-1", status: "completed", result: "done" });
const queuedJob = Object.freeze({ id: "job-1", status: "queued" });

test("BeeClient validates construction and normalizes configured transport options", async () => {
  assert.throws(() => new BeeClient({ apiKey: "" }), /apiKey is required/);
  assert.throws(() => new BeeClient({ apiKey: 42 }), /apiKey is required/);
  assert.doesNotThrow(() => new BeeClient({ apiKey }));

  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = undefined;
    assert.throws(() => new BeeClient({ apiKey }), /no fetch implementation found/);
  } finally {
    globalThis.fetch = originalFetch;
  }

  const { client, calls } = recordingClient([jsonResponse({ object: "list", data: [] })], {
    baseURL: "https://sdk.invalid/root///",
    timeoutMs: 1_234,
    headers: { "X-SDK-Test": "present", Authorization: "extra-header-must-not-win" },
  });
  await client.models.list();
  assert.equal(calls[0].url, "https://sdk.invalid/root/models");
  assert.equal(calls[0].init.headers["X-SDK-Test"], "present");
  assert.equal(calls[0].init.headers.Authorization, "extra-header-must-not-win");
  assert.equal(calls[0].init.headers.Accept, "application/json");
  assert.equal(calls[0].init.body, undefined);
  assert.equal("Content-Type" in calls[0].init.headers, false);
});

test("chat completion forwards every supported optional parameter", async () => {
  const result = { id: "completion-1", choices: [] };
  const { client, calls } = recordingClient([jsonResponse(result)]);
  assert.deepEqual(
    await client.chat.completions.create({
      model: "bee-hive",
      domain: "quantum",
      messages: [{ role: "user", content: [{ type: "text", text: "select" }] }],
      temperature: 0,
      max_tokens: 0,
      seed: 0,
      stream: false,
    }),
    result,
  );
  assert.deepEqual(JSON.parse(calls[0].init.body), {
    model: "bee-hive",
    messages: [{ role: "user", content: [{ type: "text", text: "select" }] }],
    domain: "quantum",
    temperature: 0,
    max_tokens: 0,
    seed: 0,
  });
  assert.equal(calls[0].init.headers["Content-Type"], "application/json");
});

test("chat completion applies defaults and validates message contracts before transport", async () => {
  const { client, calls } = recordingClient([jsonResponse({ id: "defaulted" })]);
  await client.chat.completions.create({ messages: [{ role: "user", content: "hello" }] });
  assert.deepEqual(JSON.parse(calls[0].init.body), {
    model: "bee-cell",
    messages: [{ role: "user", content: "hello" }],
  });

  const invalid = [
    { messages: undefined, message: "messages must be a non-empty array" },
    { messages: [], message: "messages must be a non-empty array" },
    { messages: [null], message: "each message must have a string `role`" },
    { messages: [{ role: 1, content: "x" }], message: "each message must have a string `role`" },
    { messages: [{ role: "user", content: 1 }], message: "each message `content` must be a string or array of parts" },
  ];
  for (const { messages, message } of invalid) {
    await assert.rejects(
      () => client.chat.completions.create({ messages }),
      (error) => error instanceof Error && error.message === `BeeClient: ${message}`,
    );
  }
  assert.equal(calls.length, 1);
});

test("streaming chat parses split SSE events, skips malformed input, and stops at DONE", async () => {
  const encoder = new TextEncoder();
  const chunks = [
    ": heartbeat\n\n\ndata: not-json\n\n",
    "event: message\ndata: {\"id\":\"chunk-1\",\"choices\":[]}",
    "\n\ndata: [DONE]\n\n",
  ];
  const body = new ReadableStream({
    pull(controller) {
      const chunk = chunks.shift();
      if (chunk === undefined) controller.close();
      else controller.enqueue(encoder.encode(chunk));
    },
  });
  const { client, calls } = recordingClient([new Response(body)]);
  const stream = await client.chat.completions.create({
    messages: [{ role: "user", content: "stream" }],
    stream: true,
  });
  const received = [];
  for await (const chunk of stream) received.push(chunk);

  assert.deepEqual(received, [{ id: "chunk-1", choices: [] }]);
  assert.equal(calls[0].init.headers.Accept, "text/event-stream");
  assert.equal(JSON.parse(calls[0].init.body).stream, true);
});

test("streaming chat handles EOF and rejects a successful response without a body", async () => {
  const { client } = recordingClient([
    new Response("data: {\"id\":\"chunk-eof\",\"choices\":[]}\n\n"),
    new Response(null),
  ]);
  const stream = await client.chat.completions.create({
    messages: [{ role: "user", content: "stream" }],
    stream: true,
  });
  const received = [];
  for await (const chunk of stream) received.push(chunk);
  assert.deepEqual(received, [{ id: "chunk-eof", choices: [] }]);

  const bodyless = await client.chat.completions.create({
    messages: [{ role: "user", content: "stream" }],
    stream: true,
  });
  await assert.rejects(async () => {
    for await (const _chunk of bodyless) assert.fail("bodyless stream yielded a chunk");
  }, (error) => error instanceof BeeError && error.status === 200 && error.body === null);
});

test("request timeout maps aborts while unrelated transport failures pass through", async () => {
  const timeoutClient = clientWith(
    async (_url, init) =>
      await new Promise((_resolve, reject) => {
        init.signal.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")), {
          once: true,
        });
      }),
    { timeoutMs: 1 },
  );
  await assert.rejects(
    () => timeoutClient.models.list(),
    (error) => error instanceof BeeTimeoutError && error.status === 0 && error.body.timeoutMs === 1,
  );

  const transportError = new Error("transport failed");
  const failingClient = clientWith(async () => {
    throw transportError;
  });
  await assert.rejects(() => failingClient.models.list(), (error) => error === transportError);
});

test("request errors map authentication, rate limiting, and generic failures", async () => {
  const responses = [
    jsonResponse({ error: "unauthorized" }, { status: 401 }),
    jsonResponse({ error: "forbidden" }, { status: 403 }),
    jsonResponse({ error: "slow down" }, { status: 429, headers: { "retry-after": "17" } }),
    jsonResponse({ error: "slow down" }, { status: 429, headers: { "retry-after": "later" } }),
    jsonResponse({ error: "bad request" }, { status: 400 }),
  ];
  const { client } = recordingClient(responses);

  for (const status of [401, 403]) {
    await assert.rejects(
      () => client.models.list(),
      (error) => error instanceof BeeAuthError && error.status === status && error.name === "BeeAuthError",
    );
  }
  await assert.rejects(
    () => client.models.list(),
    (error) => error instanceof BeeRateLimitError && error.retryAfterSeconds === 17,
  );
  await assert.rejects(
    () => client.models.list(),
    (error) => error instanceof BeeRateLimitError && error.retryAfterSeconds === null,
  );
  await assert.rejects(
    () => client.models.list(),
    (error) => error instanceof BeeError && error.constructor === BeeError && error.status === 400,
  );
});

test("structured action decisions take precedence and malformed decision fields do not", async () => {
  const decision = {
    schema_version: "2026-07-31",
    reason: "insufficient_credits",
    current_plan: "api-free",
    required_plan: null,
    actions: [],
  };
  const malformedBodies = [
    { bee_upgrade: null },
    { bee_upgrade: "upgrade" },
    { other: true },
  ];
  const { client } = recordingClient([
    jsonResponse({ bee_upgrade: decision }, { status: 402 }),
    ...malformedBodies.map((body) => jsonResponse(body, { status: 402 })),
  ]);
  await assert.rejects(
    () => client.models.list(),
    (error) => {
      assert.ok(error instanceof BeeActionRequiredError);
      assert.equal(error.name, "BeeActionRequiredError");
      assert.deepEqual(error.decision, decision);
      return true;
    },
  );
  for (const body of malformedBodies) {
    await assert.rejects(
      () => client.models.list(),
      (error) => error instanceof BeeError && !(error instanceof BeeActionRequiredError) && error.body.bee_upgrade === body.bee_upgrade,
    );
  }
});

test("error body reading falls back to text and then null", async () => {
  const textResponse = {
    ok: false,
    status: 502,
    headers: new Headers(),
    json: async () => { throw new SyntaxError("not JSON"); },
    text: async () => "gateway unavailable",
  };
  const nullResponse = {
    ok: false,
    status: 503,
    headers: new Headers(),
    json: async () => { throw new SyntaxError("not JSON"); },
    text: async () => { throw new Error("body unavailable"); },
  };
  const { client } = recordingClient([textResponse, nullResponse]);
  await assert.rejects(
    () => client.models.list(),
    (error) => error instanceof BeeError && error.body === "gateway unavailable",
  );
  await assert.rejects(
    () => client.models.list(),
    (error) => error instanceof BeeError && error.body === null,
  );
});

test("all request error classes expose stable names and structured fields", () => {
  const base = new BeeError("base", 500, { code: "failure" });
  const auth = new BeeAuthError("auth", 403, null);
  const rate = new BeeRateLimitError("rate", { code: "limited" }, 3);
  const timeout = new BeeTimeoutError("timeout", 50);
  assert.deepEqual(
    [base.name, auth.name, rate.name, timeout.name],
    ["BeeError", "BeeAuthError", "BeeRateLimitError", "BeeTimeoutError"],
  );
  assert.deepEqual([base.status, auth.status, rate.status, timeout.status], [500, 403, 429, 0]);
});

test("quantum reasoning job operations encode inputs and preserve response contracts", async () => {
  const listResult = { jobs: [], capabilities: { products: [] }, next_cursor: null };
  const removed = { ok: true, status: "deleted" };
  const { client, calls } = recordingClient([
    jsonResponse({ job: completedJob }),
    jsonResponse({ job: completedJob }),
    jsonResponse(listResult),
    jsonResponse(listResult),
    jsonResponse({ job: completedJob }),
    jsonResponse(removed),
  ]);

  assert.deepEqual(
    await client.quantumReasoning.jobs.create({
      prompt: "reason",
      model: "bee-hive",
      product: "simulation_cloud",
      provider_connection_id: null,
      workspace_id: "workspace-1",
      idempotency_key: "idempotency-key-1",
    }),
    completedJob,
  );
  assert.deepEqual(
    await client.quantumReasoning.jobs.create({
      prompt: "reason again",
      model: "bee-swarm",
      product: "managed_qpu",
    }),
    completedJob,
  );
  assert.deepEqual(await client.quantumReasoning.jobs.list(), listResult);
  assert.deepEqual(
    await client.quantumReasoning.jobs.list({
      cursor: "cursor value",
      limit: 0,
      status: "queued",
      model: "bee-hive",
    }),
    listResult,
  );
  assert.deepEqual(await client.quantumReasoning.jobs.retrieve("job/id"), completedJob);
  assert.deepEqual(await client.quantumReasoning.jobs.remove("job/id"), removed);

  assert.deepEqual(JSON.parse(calls[0].init.body), {
    prompt: "reason",
    model: "bee-hive",
    product: "simulation_cloud",
    provider_connection_id: null,
    workspace_id: "workspace-1",
  });
  assert.equal(calls[0].init.headers["Idempotency-Key"], "idempotency-key-1");
  assert.match(calls[1].init.headers["Idempotency-Key"], /^[0-9a-f-]{36}$/);
  assert.deepEqual(JSON.parse(calls[1].init.body), {
    prompt: "reason again",
    model: "bee-swarm",
    product: "managed_qpu",
  });
  assert.equal(calls[2].url.endsWith("/quantum-reasoning/jobs"), true);
  assert.equal(
    calls[3].url.endsWith("/quantum-reasoning/jobs?cursor=cursor+value&limit=0&status=queued&model=bee-hive"),
    true,
  );
  assert.equal(calls[4].url.endsWith("/quantum-reasoning/jobs/job%2Fid"), true);
  assert.equal(calls[5].init.method, "DELETE");
});

test("quantum reasoning create rejects missing and whitespace-only prompts", async () => {
  const client = clientWith(async () => assert.fail("invalid prompt reached transport"));
  await assert.rejects(
    () => client.quantumReasoning.jobs.create({ prompt: "", model: "bee-hive", product: "simulation_cloud" }),
    /prompt is required/,
  );
  await assert.rejects(
    () => client.quantumReasoning.jobs.create({ prompt: "   ", model: "bee-hive", product: "simulation_cloud" }),
    /prompt is required/,
  );
});

test("quantum reasoning wait validates timing and returns terminal jobs", async () => {
  const { client } = recordingClient([jsonResponse({ job: completedJob })]);
  await assert.rejects(() => client.quantumReasoning.jobs.wait("job-1", { timeout_ms: 0 }), /must be positive/);
  await assert.rejects(
    () => client.quantumReasoning.jobs.wait("job-1", { poll_interval_ms: 0 }),
    /must be positive/,
  );
  assert.deepEqual(await client.quantumReasoning.jobs.wait("job-1"), completedJob);
});

test("quantum reasoning wait polls active jobs and times out deterministically", async () => {
  const polling = recordingClient([
    jsonResponse({ job: queuedJob }),
    jsonResponse({ job: completedJob }),
  ]).client;
  assert.deepEqual(
    await polling.quantumReasoning.jobs.wait("job-1", { timeout_ms: 100, poll_interval_ms: 1 }),
    completedJob,
  );

  const timingOut = recordingClient([jsonResponse({ job: queuedJob })]).client;
  await assert.rejects(
    () => timingOut.quantumReasoning.jobs.wait("job-1", { timeout_ms: 1, poll_interval_ms: 5 }),
    /timed out waiting for quantum reasoning job job-1/,
  );
});

test("quantum reasoning wait honors already-aborted signals with and without reasons", async () => {
  const client = clientWith(async () => assert.fail("aborted wait reached transport"));
  const reason = new Error("caller stopped");
  const withReason = AbortSignal.abort(reason);
  await assert.rejects(
    () => client.quantumReasoning.jobs.wait("job-1", { signal: withReason }),
    (error) => error === reason,
  );

  const controller = new AbortController();
  controller.abort();
  await assert.rejects(
    () => client.quantumReasoning.jobs.wait("job-1", { signal: controller.signal }),
    (error) => error === controller.signal.reason,
  );
});

test("quantum reasoning wait detects aborts after retrieval and during polling sleep", async () => {
  const afterRetrieveController = new AbortController();
  const afterRetrieve = clientWith(async () => {
    afterRetrieveController.abort(new Error("aborted after retrieval"));
    return jsonResponse({ job: queuedJob });
  });
  await assert.rejects(
    () => afterRetrieve.quantumReasoning.jobs.wait("job-1", { signal: afterRetrieveController.signal }),
    /aborted after retrieval/,
  );

  const duringSleepController = new AbortController();
  const duringSleep = recordingClient([jsonResponse({ job: queuedJob })]).client;
  const wait = duringSleep.quantumReasoning.jobs.wait("job-1", {
    timeout_ms: 1_000,
    poll_interval_ms: 500,
    signal: duringSleepController.signal,
  });
  setTimeout(() => duringSleepController.abort(new Error("aborted during sleep")), 5);
  await assert.rejects(() => wait, /aborted during sleep/);
});

test("provenance validates session IDs and URL-encodes valid identifiers", async () => {
  const expected = { session_id: "session/id", verified: true, chain: [] };
  const { client, calls } = recordingClient([jsonResponse(expected)]);
  await assert.rejects(() => client.provenance.verify(""), /requires a session id/);
  await assert.rejects(() => client.provenance.verify(7), /requires a session id/);
  assert.deepEqual(await client.provenance.verify("session/id"), expected);
  assert.equal(calls[0].url.endsWith("/provenance/session%2Fid"), true);
});

test("usage retrieves canonical day and week windows", async () => {
  const day = { breakdown: { window: "day" } };
  const week = { breakdown: { window: "week" } };
  const { client, calls } = recordingClient([
    jsonResponse(day),
    jsonResponse(week),
    jsonResponse(day),
  ]);
  assert.deepEqual(await client.usage.retrieve(), day);
  assert.deepEqual(await client.usage.retrieve("week"), week);
  assert.deepEqual(await client.usage.retrieve("unsupported"), day);
  assert.deepEqual(
    calls.map(({ url }) => new URL(url).search),
    ["?window=day", "?window=week", "?window=day"],
  );
});

test("quantum reasoning wait supplies fallback abort errors and cleans up live listeners", async () => {
  const initiallyAborted = { aborted: true, reason: undefined };
  const noTransport = clientWith(async () => assert.fail("initial abort reached transport"));
  await assert.rejects(
    () => noTransport.quantumReasoning.jobs.wait("job-1", { signal: initiallyAborted }),
    (error) => error instanceof Error && error.message === "Aborted",
  );

  const abortedAfterRetrieve = {
    aborted: false,
    reason: undefined,
    addEventListener() {},
    removeEventListener() {},
  };
  const afterRetrieve = clientWith(async () => {
    abortedAfterRetrieve.aborted = true;
    return jsonResponse({ job: queuedJob });
  });
  await assert.rejects(
    () => afterRetrieve.quantumReasoning.jobs.wait("job-1", { signal: abortedAfterRetrieve }),
    (error) => error instanceof Error && error.message === "Aborted",
  );

  let abortListener;
  const abortDuringSleep = {
    aborted: false,
    reason: undefined,
    addEventListener(_type, listener) {
      abortListener = listener;
      queueMicrotask(listener);
    },
    removeEventListener() {},
  };
  const sleeping = recordingClient([jsonResponse({ job: queuedJob })]).client;
  await assert.rejects(
    () => sleeping.quantumReasoning.jobs.wait("job-1", { signal: abortDuringSleep }),
    (error) => error instanceof Error && error.message === "Aborted",
  );
  assert.equal(typeof abortListener, "function");

  let removals = 0;
  const liveSignal = {
    aborted: false,
    reason: undefined,
    addEventListener() {},
    removeEventListener(type) {
      assert.equal(type, "abort");
      removals += 1;
    },
  };
  const polling = recordingClient([
    jsonResponse({ job: queuedJob }),
    jsonResponse({ job: completedJob }),
  ]).client;
  assert.deepEqual(
    await polling.quantumReasoning.jobs.wait("job-1", {
      timeout_ms: 100,
      poll_interval_ms: 1,
      signal: liveSignal,
    }),
    completedJob,
  );
  assert.equal(removals, 1);
});