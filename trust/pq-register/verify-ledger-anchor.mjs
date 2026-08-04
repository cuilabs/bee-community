#!/usr/bin/env node
// Re-runnable proof that the PQ coverage-register key ceremony is anchored in the
// QNSI audit ledger — the first of the three independent pinning surfaces named in
// meta.signing.public_key_publication ("the QNSI audit ledger (fingerprint anchored
// at the key ceremony)").
//
// It reads the committed signature envelope (source of truth for the fingerprint +
// canonical register hash), queries the live QNSI audit ledger for the ceremony
// anchor event, and asserts the anchored values match the envelope. Read-only and
// idempotent — safe to run any number of times.
//
//   QNSI_BEE_PLATFORM_KEY=... node trust/pq-register/verify-ledger-anchor.mjs
//
// Exit 0 = anchored & matching; 1 = missing/mismatch; 2 = usage/config error.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const BASE = process.env.QNSI_PLATFORM_URL ?? "https://api.qnsi.heossi.com";
const KEY = process.env.QNSI_BEE_PLATFORM_KEY ?? "";
const TOPIC = "pqc.register.key_ceremony_anchor";

function fail(code, msg) {
  console.error(msg);
  process.exit(code);
}

if (!KEY) {
  fail(2, "QNSI_BEE_PLATFORM_KEY is required (tenant-scoped read key for the QNSI audit ledger).");
}

// Source of truth: the committed detached signature envelope for the current version.
const meta = JSON.parse(readFileSync(join(HERE, "bee-pq-register.json"), "utf8"));
const version = meta.meta.version;
const envelope = JSON.parse(
  readFileSync(join(HERE, `bee-pq-register.v${version}.sig.json`), "utf8"),
);
const expected = {
  fingerprint: envelope.public_key_fingerprint,
  registerHash: envelope.register_hash,
  keyId: envelope.key_id,
  algorithm: envelope.algorithm,
};

async function main() {
  const url = `${BASE}/proxy/audit/v1/events?topic=${encodeURIComponent(TOPIC)}&limit=20`;
  const res = await fetch(url, {
    headers: { authorization: `Bearer ${KEY}` },
    signal: AbortSignal.timeout(30_000),
  });
  if (!res.ok) {
    fail(1, `QNSI audit query failed: HTTP ${res.status} ${await res.text().catch(() => "")}`);
  }
  const body = await res.json();
  const items = body.items ?? body.events ?? (Array.isArray(body) ? body : []);

  const match = items.find((e) => {
    const p = e.payload ?? {};
    return p.public_key_fingerprint === expected.fingerprint && p.register_hash === expected.registerHash;
  });

  if (!match) {
    fail(
      1,
      `NOT ANCHORED: no QNSI audit event on topic '${TOPIC}' carries fingerprint ${expected.fingerprint} + register_hash ${expected.registerHash} (register v${version}). Found ${items.length} anchor event(s).`,
    );
  }

  const cc = match.payload?.cryptoContext ?? {};
  console.log("PASS — register key ceremony is anchored in the QNSI audit ledger.");
  console.log(`  register version:     v${version}`);
  console.log(`  ledger event id:      ${match.id}`);
  console.log(`  topic:                ${match.topic}`);
  console.log(`  received at:          ${match.receivedAt ?? match.received_at ?? "?"}`);
  console.log(`  fingerprint:          ${match.payload.public_key_fingerprint}`);
  console.log(`  register_hash:        ${match.payload.register_hash}`);
  console.log(`  key_id / algorithm:   ${cc.keyId ?? "?"} / ${cc.algorithm ?? "?"}`);
  console.log(`  event_hash present:   ${Boolean(match.eventHash ?? match.event_hash)}`);

  // The anchored values must equal the committed envelope exactly.
  const problems = [];
  if (match.payload.public_key_fingerprint !== expected.fingerprint) problems.push("fingerprint");
  if (match.payload.register_hash !== expected.registerHash) problems.push("register_hash");
  if (cc.keyId && cc.keyId !== expected.keyId) problems.push("key_id");
  if (cc.algorithm && cc.algorithm !== expected.algorithm) problems.push("algorithm");
  if (problems.length) {
    fail(1, `MISMATCH against committed envelope: ${problems.join(", ")}`);
  }
  process.exit(0);
}

main().catch((err) => fail(1, `error: ${err?.message ?? err}`));
