#!/usr/bin/env python3
"""Ceremony signer for the post-quantum coverage register.

Two subcommands:

  keygen  — generate an ML-DSA keypair. Writes <name>.pub (base64 public
            key) and <name>.key (base64 secret key, mode 0600). The
            production ceremony runs this on the offline machine; the
            secret key never leaves it.

  sign    — validate a register, compute its canonical hash, sign the
            ASCII bytes of "sha384:<hex>" with the given secret key, and
            emit the detached signature envelope
            (<register-basename>.v<version>.sig.json) conforming to
            signature-envelope.schema.json. Refuses to sign a register
            that fails schema or cross-reference validation: an invalid
            register cannot acquire a signature.

Signer roles: pass --signer offline-root for full-authority version
signatures, --signer online-downgrade for the KMS-held downgrade signer.
The role is recorded in the envelope; verifiers enforce the authority
limits (an online-downgrade envelope over a non-downgrade diff must be
rejected).

Exit codes: 0 = success; 1 = register invalid / verification failure;
2 = usage/IO error.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from mldsa import resolve
from validate_register import (
    canonical_bytes,
    cross_reference_errors,
    downgrade_diff_errors,
    load_json,
    schema_errors,
)


def fingerprint(public_key: bytes) -> str:
    return "sha384:" + hashlib.sha384(public_key).hexdigest()


def _is_test_key(key_id: str) -> bool:
    return "TEST" in key_id.upper()


def cmd_keygen(args: argparse.Namespace) -> int:
    backend = resolve(args.algorithm)
    public_key, secret_key = backend.keygen()

    pub_path = Path(f"{args.name}.pub")
    key_path = Path(f"{args.name}.key")
    pub_path.write_text(base64.b64encode(public_key).decode("ascii") + "\n", encoding="ascii")
    key_path.write_text(base64.b64encode(secret_key).decode("ascii") + "\n", encoding="ascii")
    os.chmod(key_path, 0o600)

    print(f"backend:              {backend.name}")
    print(f"algorithm:            {args.algorithm}")
    print(f"public key:           {pub_path} ({len(public_key)} bytes)")
    print(f"secret key:           {key_path} (mode 0600 — ceremony keys stay on the offline machine)")
    print(f"public key fingerprint: {fingerprint(public_key)}")
    print("pin this fingerprint at the publication surfaces before distributing signatures.")
    return 0


def cmd_sign(args: argparse.Namespace) -> int:
    register = load_json(args.register)
    schema = load_json(args.schema)

    errors = schema_errors(register, schema) + cross_reference_errors(register)
    if errors:
        for err in errors:
            print(f"FAIL  {err}", file=sys.stderr)
        print(f"refusing to sign: register is INVALID ({len(errors)} error(s))", file=sys.stderr)
        return 1

    backend = resolve(args.algorithm)
    if backend.name != "liboqs" and not _is_test_key(args.key_id):
        print(f"FAIL  production-signing guard: backend '{backend.name}' is pure Python and not constant-time — "
              f"signing with non-TEST key id '{args.key_id}' requires liboqs. "
              "Install liboqs-python on the ceremony machine, or use a key id containing 'TEST' for rehearsals.",
              file=sys.stderr)
        return 1

    if args.signer == "online-downgrade":
        if args.predecessor is None:
            print("FAIL  --signer online-downgrade requires --predecessor: the downgrade authority check "
                  "runs before signing", file=sys.stderr)
            return 2
        predecessor = load_json(args.predecessor)
        predecessor_digest = hashlib.sha384(canonical_bytes(predecessor)).hexdigest()
        auth_errors = downgrade_diff_errors(predecessor, register, predecessor_digest)
        if auth_errors:
            for err in auth_errors:
                print(f"FAIL  {err}", file=sys.stderr)
            print("refusing to sign: diff exceeds online-downgrade authority — use the offline root for this change",
                  file=sys.stderr)
            return 1

    secret_key = base64.b64decode(args.secret_key.read_text(encoding="ascii").strip())
    public_key = base64.b64decode(args.public_key.read_text(encoding="ascii").strip())

    digest = hashlib.sha384(canonical_bytes(register)).hexdigest()
    register_hash = f"sha384:{digest}"
    signature = backend.sign(secret_key, register_hash.encode("ascii"))

    if not backend.verify(public_key, register_hash.encode("ascii"), signature):
        print("FAIL  self-check: freshly produced signature does not verify against the supplied public key "
              "(key mismatch or backend fault) — no envelope written", file=sys.stderr)
        return 1

    version = register["meta"]["version"]
    envelope = {
        "envelope_version": "1.0.0",
        "register_version": version,
        "register_hash": register_hash,
        "algorithm": args.algorithm,
        "signer": args.signer,
        "key_id": args.key_id,
        "public_key_fingerprint": fingerprint(public_key),
        "public_key": base64.b64encode(public_key).decode("ascii"),
        "signature": base64.b64encode(signature).decode("ascii"),
        "signed_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "predecessor_envelope_hash": args.predecessor_envelope_hash,
    }

    out = args.out or args.register.with_name(f"{args.register.stem}.v{version}.sig.json")
    out.write_text(json.dumps(envelope, indent=2) + "\n", encoding="utf-8")

    print(f"backend:         {backend.name}")
    print(f"signed:          {out}")
    print(f"register:        {version}  hash {register_hash}")
    print(f"signer:          {args.signer}  key_id {args.key_id}")
    print(f"signature:       {len(signature)} bytes ML-DSA, verified before writing")
    print("next: anchor the envelope hash and key fingerprint in the QNSI audit ledger, "
          "publish the envelope alongside the register, and confirm the fingerprint at two pinning surfaces.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Sign a post-quantum coverage register (detached envelope).")
    sub = parser.add_subparsers(dest="command", required=True)

    kg = sub.add_parser("keygen", help="Generate an ML-DSA keypair")
    kg.add_argument("--algorithm", choices=["ML-DSA-65", "ML-DSA-87"], default="ML-DSA-65")
    kg.add_argument("--name", required=True, help="Output basename: writes <name>.pub and <name>.key")
    kg.set_defaults(func=cmd_keygen)

    sg = sub.add_parser("sign", help="Sign a validated register, emitting the detached envelope")
    sg.add_argument("register", type=Path, help="Path to the register JSON instance")
    sg.add_argument("--schema", type=Path, default=Path(__file__).with_name("register.schema.json"))
    sg.add_argument("--algorithm", choices=["ML-DSA-65", "ML-DSA-87"], default="ML-DSA-65")
    sg.add_argument("--secret-key", type=Path, required=True, help="Base64 secret-key file from keygen")
    sg.add_argument("--public-key", type=Path, required=True, help="Base64 public-key file from keygen")
    sg.add_argument("--signer", choices=["offline-root", "online-downgrade"], required=True)
    sg.add_argument("--predecessor", type=Path, default=None,
                    help="Predecessor register JSON (required for --signer online-downgrade: the authority "
                         "diff check runs before signing)")
    sg.add_argument("--key-id", required=True, help="Stable key identifier recorded in the envelope")
    sg.add_argument("--predecessor-envelope-hash", default=None,
                    help="sha384:<hex> of the previous envelope file; omit for the first signed version")
    sg.add_argument("--out", type=Path, default=None, help="Envelope output path (default: <register>.v<version>.sig.json)")
    sg.set_defaults(func=cmd_sign)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
