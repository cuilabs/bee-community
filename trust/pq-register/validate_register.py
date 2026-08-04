#!/usr/bin/env python3
"""Validate a post-quantum coverage register against the open specification.

Performs three layers of verification:
  1. JSON Schema conformance (register.schema.json).
  2. Cross-reference integrity that a schema cannot express:
     probe/row/gate reference closure, covered-row probe binding,
     changelog/version agreement, evidence discipline.
  3. Canonical serialization and SHA-384 hash — the exact signing
     preimage referenced in meta.signing.canonicalization.

Exit codes: 0 = valid; 1 = validation failure; 2 = usage/IO error.
This tool is part of the published probe suite: third parties run it
against the fetched register to verify structure before checking the
ML-DSA signature over the canonical hash it prints.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


def load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as exc:
        print(f"error: {path} is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(2)


def canonical_bytes(register: dict) -> bytes:
    """Deterministic serialization per meta.signing.canonicalization:
    UTF-8 JSON, lexicographically sorted keys, compact separators."""
    return json.dumps(
        register, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def schema_errors(register: dict, schema: dict) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"schema: {'/'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
        for err in sorted(validator.iter_errors(register), key=lambda e: list(e.absolute_path))
    ]


def cross_reference_errors(register: dict) -> list[str]:
    errors: list[str] = []

    rows = register.get("rows", [])
    probes = register.get("probes", [])
    gates = register.get("gates", [])

    row_ids = [r.get("id") for r in rows]
    probe_ids = [p.get("id") for p in probes]
    gate_ids = [g.get("id") for g in gates]

    for label, ids in (("row", row_ids), ("probe", probe_ids), ("gate", gate_ids)):
        seen: set[str] = set()
        for identifier in ids:
            if identifier in seen:
                errors.append(f"xref: duplicate {label} id {identifier}")
            seen.add(identifier)

    row_id_set, probe_id_set, gate_id_set = set(row_ids), set(probe_ids), set(gate_ids)

    for row in rows:
        rid = row.get("id", "<missing>")
        for pid in row.get("probes", []):
            if pid not in probe_id_set:
                errors.append(f"xref: {rid} references undefined probe {pid}")
        gate = row.get("gate")
        if gate and gate not in gate_id_set:
            errors.append(f"xref: {rid} references undefined gate {gate}")
        if row.get("status") == "covered" and not row.get("probes"):
            errors.append(f"xref: {rid} is covered but bound to no probe — covered status requires a probe")
        if row.get("status") == "excluded":
            if row.get("probes"):
                errors.append(f"xref: {rid} is excluded but lists probes — excluded rows carry no mechanism to probe")
            if row.get("closure") == "permanent" and not row.get("boundary_statement", False):
                errors.append(f"xref: {rid} is permanently excluded but not marked boundary_statement — permanent exclusions must be boundary statements")
        for ev in row.get("evidence", []):
            if ev.get("ships") == "live" and "url" not in ev:
                errors.append(f"xref: {rid} evidence '{ev.get('label')}' is marked live but has no URL")

    for probe in probes:
        pid = probe.get("id", "<missing>")
        scope = probe.get("scope", "mechanism")
        declared = set(probe.get("verifies_rows", []))
        bound = {r["id"] for r in rows if pid in r.get("probes", [])}
        for rid in declared:
            if rid not in row_id_set:
                errors.append(f"xref: {pid} claims to verify undefined row {rid}")
        if not probe.get("published", False):
            errors.append(f"xref: {pid} is not published — probes must be published for third-party execution")
        if scope == "mechanism":
            missing_back = (declared & row_id_set) - bound
            if missing_back:
                errors.append(
                    f"xref: mechanism probe {pid} declares rows {sorted(missing_back)} that do not bind it back — binding must be bidirectional"
                )
            undeclared = bound - declared
            if undeclared:
                errors.append(
                    f"xref: mechanism probe {pid} is bound by rows {sorted(undeclared)} but does not declare them in verifies_rows"
                )
        else:
            if bound:
                errors.append(
                    f"xref: meta probe {pid} is bound by rows {sorted(bound)} — meta-probes verify register infrastructure, not row mechanisms, and must not be row-bound"
                )

    for gate in gates:
        automated_by = gate.get("automated_by")
        if automated_by and automated_by not in probe_id_set:
            errors.append(f"xref: gate {gate.get('id')} automated_by references undefined probe {automated_by}")

    changelog = register.get("changelog", [])
    meta_version = register.get("meta", {}).get("version")
    if changelog and meta_version:
        latest = changelog[-1].get("version")
        if latest != meta_version:
            errors.append(
                f"xref: meta.version {meta_version} does not match latest changelog entry {latest}"
            )

    return errors


def downgrade_diff_errors(predecessor: dict, register: dict, predecessor_digest: str) -> list[str]:
    """Verify that `register` differs from `predecessor` only within the
    predecessor's downgrade_diff_policy. Used to bound the online-downgrade
    signer's authority: any out-of-whitelist change invalidates it."""
    errors: list[str] = []

    if register.get("meta", {}).get("predecessor_hash") != f"sha384:{predecessor_digest}":
        return [
            "downgrade-auth: register.meta.predecessor_hash does not match the supplied predecessor's "
            "computed canonical hash — cannot establish a trusted diff baseline"
        ]

    policy = predecessor.get("meta", {}).get("signing", {}).get("downgrade_diff_policy")
    if not policy:
        return ["downgrade-auth: predecessor defines no downgrade_diff_policy — online-downgrade signatures cannot be authorized"]

    allowed_meta = set(policy["allowed_meta_fields"])
    allowed_row_fields = set(policy["allowed_row_fields"])
    transitions = {(t["from"], t["to"]) for t in policy["allowed_status_transitions"]}

    for section in ("profiles", "probes", "probe_semantics", "gates"):
        if predecessor.get(section) != register.get(section):
            errors.append(f"downgrade-auth: section '{section}' changed — not permitted under online-downgrade authority")

    pm, nm = predecessor["meta"], register["meta"]
    for key in sorted(set(pm) | set(nm)):
        if key in allowed_meta:
            continue
        if pm.get(key) != nm.get(key):
            errors.append(f"downgrade-auth: meta.{key} changed — not permitted under online-downgrade authority")

    p_ids = [r["id"] for r in predecessor["rows"]]
    n_ids = [r["id"] for r in register["rows"]]
    if p_ids != n_ids:
        errors.append("downgrade-auth: row set or row order changed — not permitted under online-downgrade authority")
    else:
        for pr, nr in zip(predecessor["rows"], register["rows"]):
            for key in sorted(set(pr) | set(nr)):
                if pr.get(key) == nr.get(key):
                    continue
                if key not in allowed_row_fields:
                    errors.append(f"downgrade-auth: {pr['id']}.{key} changed — not permitted under online-downgrade authority")
                elif key == "status" and (pr["status"], nr["status"]) not in transitions:
                    errors.append(
                        f"downgrade-auth: {pr['id']} status {pr['status']} → {nr['status']} is not a permitted downgrade transition"
                    )

    pcl, ncl = predecessor["changelog"], register["changelog"]
    if ncl[: len(pcl)] != pcl:
        errors.append("downgrade-auth: changelog history rewritten — changelog must be append-only")
    else:
        for entry in ncl[len(pcl):]:
            if not entry.get("probe_initiated", False):
                errors.append(
                    f"downgrade-auth: appended changelog entry {entry.get('version')} not marked probe_initiated — "
                    "online-downgrade versions may append probe-initiated entries only"
                )
    return errors


def envelope_errors(envelope: dict, envelope_schema: dict, register: dict, digest: str) -> list[str]:
    errors = [
        f"envelope-schema: {'/'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
        for err in Draft202012Validator(envelope_schema, format_checker=FormatChecker()).iter_errors(envelope)
    ]
    if not errors:
        if envelope["register_hash"] != f"sha384:{digest}":
            errors.append(
                f"envelope: register_hash {envelope['register_hash']} does not match computed canonical hash sha384:{digest}"
            )
        if envelope["register_version"] != register["meta"]["version"]:
            errors.append(
                f"envelope: register_version {envelope['register_version']} does not match register meta.version {register['meta']['version']}"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a post-quantum coverage register.")
    parser.add_argument("register", type=Path, help="Path to the register JSON instance")
    parser.add_argument("--schema", type=Path, default=Path(__file__).with_name("register.schema.json"),
                        help="Path to register.schema.json (default: alongside this script)")
    parser.add_argument("--envelope", type=Path, default=None,
                        help="Optional detached signature envelope to verify against this register")
    parser.add_argument("--envelope-schema", type=Path,
                        default=Path(__file__).with_name("signature-envelope.schema.json"),
                        help="Path to signature-envelope.schema.json")
    parser.add_argument("--public-key", type=Path, default=None,
                        help="Base64 public-key file: cryptographically verify the envelope's ML-DSA signature "
                             "and check the key fingerprint (requires --envelope)")
    parser.add_argument("--predecessor", type=Path, default=None,
                        help="Predecessor register JSON: required to verify an online-downgrade envelope's "
                             "authority (diff must stay within the predecessor's downgrade_diff_policy)")
    args = parser.parse_args()

    if args.public_key and not args.envelope:
        print("error: --public-key requires --envelope", file=sys.stderr)
        return 2

    register = load_json(args.register)
    schema = load_json(args.schema)

    errors = schema_errors(register, schema) + cross_reference_errors(register)
    digest = hashlib.sha384(canonical_bytes(register)).hexdigest()

    envelope = None
    signature_verified = False
    downgrade_authority_verified = False
    backend_name = None
    if args.envelope:
        envelope = load_json(args.envelope)
        errors += envelope_errors(envelope, load_json(args.envelope_schema), register, digest)
        if not errors and envelope.get("signer") == "online-downgrade":
            if args.predecessor is None:
                errors.append(
                    "downgrade-auth: envelope is signed by the online-downgrade signer; --predecessor is required "
                    "to verify its authority — an online-downgrade envelope cannot be accepted as VALID without it"
                )
            else:
                predecessor = load_json(args.predecessor)
                predecessor_digest = hashlib.sha384(canonical_bytes(predecessor)).hexdigest()
                auth_errors = downgrade_diff_errors(predecessor, register, predecessor_digest)
                errors += auth_errors
                downgrade_authority_verified = not auth_errors
        if not errors and args.public_key:
            import base64
            from mldsa import resolve
            public_key = base64.b64decode(args.public_key.read_text(encoding="ascii").strip())
            expected_fp = "sha384:" + hashlib.sha384(public_key).hexdigest()
            if expected_fp != envelope["public_key_fingerprint"]:
                errors.append(
                    f"envelope: public-key fingerprint mismatch — supplied key is {expected_fp}, "
                    f"envelope pins {envelope['public_key_fingerprint']}"
                )
            else:
                backend = resolve(envelope["algorithm"])
                backend_name = backend.name
                signature = base64.b64decode(envelope["signature"])
                if backend.verify(public_key, envelope["register_hash"].encode("ascii"), signature):
                    signature_verified = True
                else:
                    errors.append("envelope: ML-DSA signature verification FAILED over the register hash")

    if errors:
        for err in errors:
            print(f"FAIL  {err}")
        print(f"\nresult: INVALID — {len(errors)} error(s)")
        return 1

    meta = register["meta"]
    print("result: VALID")
    print(f"register:        {meta['register_name']}")
    print(f"version:         {meta['version']} ({meta['date']})")
    print(f"rows:            {len(register['rows'])}  "
          f"(covered {sum(1 for r in register['rows'] if r['status'] == 'covered')}, "
          f"partial {sum(1 for r in register['rows'] if r['status'] == 'partial')}, "
          f"excluded {sum(1 for r in register['rows'] if r['status'] == 'excluded')})")
    print(f"probes:          {len(register['probes'])}   gates: {len(register['gates'])}")
    print(f"canonical hash:  sha384:{digest}")
    if envelope:
        print(f"envelope:        structure valid; hash and version match; signer={envelope['signer']} key_id={envelope['key_id']}")
        if envelope.get("signer") == "online-downgrade" and downgrade_authority_verified:
            print("authority:       online-downgrade diff verified against hash-bound predecessor — "
                  "all changes within downgrade_diff_policy")
        if signature_verified:
            print(f"signature:       ML-DSA signature VERIFIED cryptographically (backend: {backend_name}); "
                  "key fingerprint matches envelope")
            print("                 remaining step for full trust: confirm the fingerprint at two independent "
                  "pinning surfaces per meta.signing.public_key_publication.")
        else:
            print("                 signature not cryptographically checked (no --public-key supplied); "
                  "verify with FIPS 204 tooling against the pinned key.")
    else:
        print("note: this hash is the ML-DSA signing preimage per meta.signing.canonicalization.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
