export interface QuantumLocalAccelerator {
  backend: "customer_gpu" | string;
  run(
    probabilities: readonly number[],
    shots: number,
    seed: number,
  ): Promise<Record<string, number>>;
}

export interface QuantumLocalResult {
  selected_index: number;
  selected: string;
  probabilities: number[];
  /** Real amplitudes for the prepared, normalized state; padded to 2^qubits. */
  amplitudes: number[];
  qubits: number;
  counts: Record<string, number>;
  shots: number;
  backend: string;
}

function validateProviderCounts(counts: Record<string, number>, shots: number): void {
  const entries = Object.entries(counts);
  if (
    entries.length === 0 ||
    entries.some(
      ([key, value]) => !/^[01]{1,64}$/.test(key) || !Number.isInteger(value) || value < 0,
    ) ||
    entries.reduce((sum, [, value]) => sum + value, 0) !== shots
  ) {
    throw new Error("provider returned invalid counts");
  }
}

function finite(value: number, name: string): number {
  if (!Number.isFinite(value)) throw new TypeError(`${name} must be finite`);
  return value;
}

function validateCounts(counts: Record<string, number>, size: number, shots: number): void {
  const entries = Object.entries(counts);
  if (
    entries.length === 0 ||
    entries.some(
      ([key, value]) =>
        !/^\d+$/.test(key) || Number(key) >= size || !Number.isInteger(value) || value < 0,
    ) ||
    entries.reduce((sum, [, value]) => sum + value, 0) !== shots
  ) {
    throw new Error("accelerator returned invalid counts");
  }
}

export async function quantumLocalSelect(input: {
  candidates: readonly string[];
  scores: readonly number[];
  shots?: number;
  seed?: number;
  accelerator?: QuantumLocalAccelerator;
}): Promise<QuantumLocalResult> {
  const { candidates, scores } = input;
  if (candidates.length < 1 || candidates.length > 256 || candidates.length !== scores.length) {
    throw new RangeError("candidates and scores must have the same length from 1 to 256");
  }
  if (candidates.some((value) => !value || value.length > 256_000))
    throw new RangeError("invalid candidate");
  for (const value of scores) finite(value, "score");
  const shots = input.shots ?? 2_000;
  const seed = input.seed ?? 0xbee;
  if (!Number.isInteger(shots) || shots < 1 || shots > 100_000)
    throw new RangeError("shots out of range");
  if (!Number.isSafeInteger(seed)) throw new RangeError("seed must be a safe integer");
  const high = Math.max(...scores);
  const weights = scores.map((score) => Math.exp(score - high));
  const total = weights.reduce((sum, value) => sum + value, 0);
  const probabilities = weights.map((value) => value / total);
  const qubits = Math.max(1, Math.ceil(Math.log2(candidates.length)));
  const amplitudes = Array.from({ length: 2 ** qubits }, (_, index) =>
    index < probabilities.length ? Math.sqrt(probabilities[index]) : 0,
  );
  let counts: Record<string, number>;
  let backend = "customer_cpu";
  if (input.accelerator) {
    counts = await input.accelerator.run(probabilities, shots, seed);
    backend = input.accelerator.backend;
  } else {
    counts = {};
    let state = seed >>> 0;
    for (let shot = 0; shot < shots; shot += 1) {
      state = (Math.imul(1664525, state) + 1013904223) >>> 0;
      const sample = state / 2 ** 32;
      let cumulative = 0;
      let index = probabilities.length - 1;
      for (let candidate = 0; candidate < probabilities.length; candidate += 1) {
        cumulative += probabilities[candidate];
        if (sample < cumulative) {
          index = candidate;
          break;
        }
      }
      counts[String(index)] = (counts[String(index)] ?? 0) + 1;
    }
  }
  validateCounts(counts, candidates.length, shots);
  const selectedIndex = Number(
    Object.keys(counts).reduce((best, key) => (counts[key] > counts[best] ? key : best)),
  );
  return {
    selected_index: selectedIndex,
    selected: candidates[selectedIndex],
    probabilities,
    amplitudes,
    qubits,
    counts,
    shots,
    backend,
  };
}

export interface ByopaDirectRequest {
  circuit: string;
  shots: number;
  backend: string;
  max_cost_minor: number;
  currency: string;
}
export interface ByopaDirectResult {
  provider_job_id: string;
  backend: string;
  counts: Record<string, number>;
  billed_cost_minor?: number;
}
export interface ByopaDirectAdapter {
  quote(
    request: ByopaDirectRequest,
  ): Promise<{ cost_minor: number; currency: string; expires_at: string }>;
  run(
    request: ByopaDirectRequest,
    quote: { cost_minor: number; currency: string; expires_at: string },
  ): Promise<ByopaDirectResult>;
}

export async function executeByopaDirect(
  request: ByopaDirectRequest,
  adapter: ByopaDirectAdapter,
): Promise<ByopaDirectResult> {
  if (!request.circuit || request.circuit.length > 1_000_000)
    throw new RangeError("invalid circuit");
  if (!Number.isInteger(request.shots) || request.shots < 1 || request.shots > 100_000)
    throw new RangeError("invalid shots");
  if (!request.backend || request.backend.length > 200) throw new RangeError("invalid backend");
  if (!Number.isSafeInteger(request.max_cost_minor) || request.max_cost_minor < 0)
    throw new RangeError("invalid cost cap");
  if (!/^[A-Z]{3}$/.test(request.currency))
    throw new RangeError("currency must be uppercase ISO-4217");
  const quote = await adapter.quote(request);
  if (
    !Number.isSafeInteger(quote.cost_minor) ||
    quote.cost_minor < 0 ||
    quote.cost_minor > request.max_cost_minor ||
    quote.currency !== request.currency ||
    !/(?:Z|[+-]\d{2}:\d{2})$/.test(quote.expires_at) ||
    !Number.isFinite(Date.parse(quote.expires_at)) ||
    Date.parse(quote.expires_at) <= Date.now()
  )
    throw new Error("provider returned invalid quote");
  const result = await adapter.run(request, quote);
  if (
    !result.provider_job_id ||
    result.provider_job_id.length > 300 ||
    result.backend !== request.backend
  )
    throw new Error("provider returned invalid identity");
  validateProviderCounts(result.counts, request.shots);
  if (
    result.billed_cost_minor !== undefined &&
    (!Number.isSafeInteger(result.billed_cost_minor) ||
      result.billed_cost_minor < 0 ||
      result.billed_cost_minor > quote.cost_minor ||
      result.billed_cost_minor > request.max_cost_minor)
  )
    throw new Error("provider returned invalid bill");
  return result;
}
