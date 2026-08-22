import assert from "node:assert/strict";
import test from "node:test";

import { executeByopaDirect, quantumLocalSelect } from "../dist/index.js";

const validRequest = Object.freeze({
  circuit: "OPENQASM 3; qubit q;",
  shots: 4,
  backend: "customer-qpu",
  max_cost_minor: 25,
  currency: "USD",
});

const validQuote = Object.freeze({
  cost_minor: 20,
  currency: "USD",
  expires_at: "2999-01-01T00:00:00Z",
});

const validResult = Object.freeze({
  provider_job_id: "provider-job-1",
  backend: "customer-qpu",
  counts: { "00": 3, "11": 1 },
  billed_cost_minor: 19,
});

function adapter(overrides = {}) {
  return {
    quote: async () => validQuote,
    run: async () => validResult,
    ...overrides,
  };
}

async function rejectsWithMessage(operation, errorType, message) {
  await assert.rejects(operation, (error) => {
    assert.ok(error instanceof errorType);
    assert.equal(error.message, message);
    return true;
  });
}

test("quantumLocalSelect deterministically samples on the customer CPU", async () => {
  const first = await quantumLocalSelect({
    candidates: ["alpha", "beta", "gamma"],
    scores: [0, 1, 2],
    shots: 128,
    seed: 12345,
  });
  const second = await quantumLocalSelect({
    candidates: ["alpha", "beta", "gamma"],
    scores: [0, 1, 2],
    shots: 128,
    seed: 12345,
  });

  assert.deepEqual(first, second);
  assert.equal(first.backend, "customer_cpu");
  assert.equal(first.shots, 128);
  assert.equal(first.qubits, 2);
  assert.equal(first.amplitudes.length, 4);
  assert.equal(first.amplitudes[3], 0);
  assert.equal(Object.values(first.counts).reduce((sum, value) => sum + value, 0), 128);
  assert.equal(first.selected, first.selected_index === 0 ? "alpha" : first.selected_index === 1 ? "beta" : "gamma");
  assert.ok(Math.abs(first.probabilities.reduce((sum, value) => sum + value, 0) - 1) < 1e-12);
});

test("quantumLocalSelect accepts validated accelerator counts and default sampling options", async () => {
  const calls = [];
  const result = await quantumLocalSelect({
    candidates: ["only"],
    scores: [0],
    accelerator: {
      backend: "customer_gpu",
      async run(probabilities, shots, seed) {
        calls.push({ probabilities, shots, seed });
        return { "0": shots };
      },
    },
  });

  assert.deepEqual(calls, [{ probabilities: [1], shots: 2_000, seed: 0xbee }]);
  assert.deepEqual(result, {
    selected_index: 0,
    selected: "only",
    probabilities: [1],
    amplitudes: [1, 0],
    qubits: 1,
    counts: { "0": 2_000 },
    shots: 2_000,
    backend: "customer_gpu",
  });
});

test("quantumLocalSelect rejects malformed candidate and numeric inputs", async () => {
  const cases = [
    [{ candidates: [], scores: [] }, RangeError, "candidates and scores must have the same length from 1 to 256"],
    [{ candidates: Array(257).fill("x"), scores: Array(257).fill(0) }, RangeError, "candidates and scores must have the same length from 1 to 256"],
    [{ candidates: ["x"], scores: [0, 1] }, RangeError, "candidates and scores must have the same length from 1 to 256"],
    [{ candidates: [""], scores: [0] }, RangeError, "invalid candidate"],
    [{ candidates: ["x".repeat(256_001)], scores: [0] }, RangeError, "invalid candidate"],
    [{ candidates: ["x"], scores: [Number.POSITIVE_INFINITY] }, TypeError, "score must be finite"],
    [{ candidates: ["x"], scores: [Number.NaN] }, TypeError, "score must be finite"],
    [{ candidates: ["x"], scores: [0], shots: 0 }, RangeError, "shots out of range"],
    [{ candidates: ["x"], scores: [0], shots: 1.5 }, RangeError, "shots out of range"],
    [{ candidates: ["x"], scores: [0], shots: 100_001 }, RangeError, "shots out of range"],
    [{ candidates: ["x"], scores: [0], seed: Number.MAX_SAFE_INTEGER + 1 }, RangeError, "seed must be a safe integer"],
  ];

  for (const [input, errorType, message] of cases) {
    await rejectsWithMessage(() => quantumLocalSelect(input), errorType, message);
  }
});

test("quantumLocalSelect rejects every invalid accelerator count shape", async () => {
  const invalidCounts = [
    {},
    { bad: 4 },
    { "1": 4 },
    { "0": 1.5, "1": 2.5 },
    { "0": -1, "1": 5 },
    { "0": 3 },
  ];

  for (const counts of invalidCounts) {
    await rejectsWithMessage(
      () =>
        quantumLocalSelect({
          candidates: ["a"],
          scores: [0],
          shots: 4,
          accelerator: { backend: "customer_gpu", run: async () => counts },
        }),
      Error,
      "accelerator returned invalid counts",
    );
  }
});

test("quantumLocalSelect resolves accelerator ties by stable key order", async () => {
  const result = await quantumLocalSelect({
    candidates: ["first", "second"],
    scores: [0, 0],
    shots: 4,
    accelerator: {
      backend: "customer_gpu",
      run: async () => ({ "0": 2, "1": 2 }),
    },
  });
  assert.equal(result.selected_index, 0);
  assert.equal(result.selected, "first");
});

test("executeByopaDirect validates, quotes, executes, and returns provider evidence", async () => {
  const calls = [];
  const result = await executeByopaDirect(validRequest, {
    async quote(request) {
      calls.push(["quote", request]);
      return validQuote;
    },
    async run(request, quote) {
      calls.push(["run", request, quote]);
      return validResult;
    },
  });

  assert.equal(result, validResult);
  assert.deepEqual(calls, [
    ["quote", validRequest],
    ["run", validRequest, validQuote],
  ]);
});

test("executeByopaDirect accepts an omitted provider bill", async () => {
  const result = { ...validResult };
  delete result.billed_cost_minor;
  assert.equal(await executeByopaDirect(validRequest, adapter({ run: async () => result })), result);
});

test("executeByopaDirect rejects malformed customer requests before quoting", async () => {
  const invalidRequests = [
    [{ circuit: "" }, "invalid circuit"],
    [{ circuit: "x".repeat(1_000_001) }, "invalid circuit"],
    [{ shots: 0 }, "invalid shots"],
    [{ shots: 1.5 }, "invalid shots"],
    [{ shots: 100_001 }, "invalid shots"],
    [{ backend: "" }, "invalid backend"],
    [{ backend: "x".repeat(201) }, "invalid backend"],
    [{ max_cost_minor: -1 }, "invalid cost cap"],
    [{ max_cost_minor: 1.5 }, "invalid cost cap"],
    [{ max_cost_minor: Number.MAX_SAFE_INTEGER + 1 }, "invalid cost cap"],
    [{ currency: "usd" }, "currency must be uppercase ISO-4217"],
    [{ currency: "USDD" }, "currency must be uppercase ISO-4217"],
  ];

  for (const [override, message] of invalidRequests) {
    let quoted = false;
    await rejectsWithMessage(
      () => executeByopaDirect({ ...validRequest, ...override }, adapter({ quote: async () => { quoted = true; return validQuote; } })),
      RangeError,
      message,
    );
    assert.equal(quoted, false);
  }
});

test("executeByopaDirect rejects invalid quotes without submitting work", async () => {
  const invalidQuotes = [
    { ...validQuote, cost_minor: 1.5 },
    { ...validQuote, cost_minor: -1 },
    { ...validQuote, cost_minor: 26 },
    { ...validQuote, currency: "EUR" },
    { ...validQuote, expires_at: "2999-01-01" },
    { ...validQuote, expires_at: "not-a-dateZ" },
    { ...validQuote, expires_at: "2000-01-01T00:00:00Z" },
  ];

  for (const quote of invalidQuotes) {
    let ran = false;
    await rejectsWithMessage(
      () => executeByopaDirect(validRequest, adapter({ quote: async () => quote, run: async () => { ran = true; return validResult; } })),
      Error,
      "provider returned invalid quote",
    );
    assert.equal(ran, false);
  }
});

test("executeByopaDirect rejects invalid provider identities", async () => {
  const invalidResults = [
    { ...validResult, provider_job_id: "" },
    { ...validResult, provider_job_id: "x".repeat(301) },
    { ...validResult, backend: "different-qpu" },
  ];
  for (const result of invalidResults) {
    await rejectsWithMessage(
      () => executeByopaDirect(validRequest, adapter({ run: async () => result })),
      Error,
      "provider returned invalid identity",
    );
  }
});

test("executeByopaDirect rejects malformed provider count evidence", async () => {
  const invalidCounts = [
    {},
    { decimal: 4 },
    { ["0".repeat(65)]: 4 },
    { "0": 1.5, "1": 2.5 },
    { "0": -1, "1": 5 },
    { "0": 3 },
  ];
  for (const counts of invalidCounts) {
    await rejectsWithMessage(
      () => executeByopaDirect(validRequest, adapter({ run: async () => ({ ...validResult, counts }) })),
      Error,
      "provider returned invalid counts",
    );
  }
});

test("executeByopaDirect rejects invalid provider bills", async () => {
  const invalidBills = [1.5, -1, 21, 26, Number.MAX_SAFE_INTEGER + 1];
  for (const billed_cost_minor of invalidBills) {
    await rejectsWithMessage(
      () => executeByopaDirect(validRequest, adapter({ run: async () => ({ ...validResult, billed_cost_minor }) })),
      Error,
      "provider returned invalid bill",
    );
  }
});