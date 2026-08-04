import type { BeeUpgradeDecision } from "./types.js";
/** Base error type - every BeeError carries the HTTP status and (when present) the upstream JSON body. */
export class BeeError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "BeeError";
    this.status = status;
    this.body = body;
  }
}

/** A structured entitlement, capacity, credit, or recovery decision from Bee. */
export class BeeActionRequiredError extends BeeError {
  readonly decision: BeeUpgradeDecision;

  constructor(message: string, status: number, body: unknown, decision: BeeUpgradeDecision) {
    super(message, status, body);
    this.name = "BeeActionRequiredError";
    this.decision = decision;
  }
}

/** 401 / 403 - bad or missing API key, or the key's plan does not grant the requested tier. */
export class BeeAuthError extends BeeError {
  constructor(message: string, status: number, body: unknown) {
    super(message, status, body);
    this.name = "BeeAuthError";
  }
}

/** 429 - rate-limited. The `retryAfterSeconds` field reflects the Retry-After header when the server set it. */
export class BeeRateLimitError extends BeeError {
  readonly retryAfterSeconds: number | null;
  constructor(message: string, body: unknown, retryAfterSeconds: number | null) {
    super(message, 429, body);
    this.name = "BeeRateLimitError";
    this.retryAfterSeconds = retryAfterSeconds;
  }
}

/** AbortController fired before the response landed. */
export class BeeTimeoutError extends BeeError {
  constructor(message: string, timeoutMs: number) {
    super(message, 0, { timeoutMs });
    this.name = "BeeTimeoutError";
  }
}
