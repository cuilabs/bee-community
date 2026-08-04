#!/usr/bin/env python3
"""Release CI gate for the post-quantum coverage register.

Runs on every release candidate. A release that changes cryptographic
behavior without a corresponding signed register change must fail the
build — this gate is the enforcement point (publication gate PG-8, and
the permanent automation of the PG-4 naming lint).

Checks, in order:

  1. register        — schema + cross-reference validation of the
                       canonical register (delegates to the published
                       validator CLI, so the gate exercises the same
                       interface third parties use).
  2. envelope        — detached-signature verification, including
                       cryptographic ML-DSA verification when a public
                       key is supplied and the downgrade-authority diff
                       when the envelope is online-downgrade-signed.
  3. render          — reproducibility: re-render the register and
                       byte-compare against the committed rendering.
                       A hand-edited document fails the build.
  4. cbom            — CycloneDX CBOM conformance: every KEM/signature
                       component must use an identifier allowed by the
                       register's profiles; banned legacy identifiers
                       (pre-standard naming) fail anywhere they appear.
  5. lint            — customer-facing string lint: banned legacy
                       identifiers must not appear in the supplied
                       source paths.

Checks 2, 4 and 5 run only when their inputs are supplied; the gate
reports them as SKIPPED, never silently PASS.

Exit codes: 0 = gate pass; 1 = gate fail; 2 = usage/IO error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

BANNED_IDENTIFIERS = ("kyber", "dilithium", "sphincs+", "falcon")

UNCLASSIFIED_PRIMITIVES = {"", "other", "unknown"}

SYMMETRIC_AND_HASH_ALLOWED = {
    "AES-256", "AES-256-GCM", "SHA-384", "SHA-512", "SHA3-384", "HMAC-SHA-384", "HKDF-SHA-384",
}


REQUIRED_TOOLCHAIN_FILES = (
    "validate_register.py", "render_register.py", "sign_register.py", "mldsa.py",
    "register.schema.json", "signature-envelope.schema.json", "matrix.template.md",
)

MANIFEST_NAME = "MANIFEST.sha384"


def check_manifest(toolchain: Path) -> list[str]:
    """Verify the distribution against its integrity manifest. File existence
    alone proved insufficient: 0.9.8 shipped a manifest listing fixture files
    that were never copied into the distribution, so `shasum -c` failed on a
    set whose gate passed. The manifest is the signed-off inventory; every
    listed file must exist with a matching hash, and the required toolchain
    files must all be listed (the manifest cannot cover itself)."""
    manifest_path = toolchain / MANIFEST_NAME
    if not manifest_path.exists():
        return [f"manifest: {MANIFEST_NAME} missing beside the gate — the distribution has no integrity inventory"]

    errors: list[str] = []
    listed: dict[str, str] = {}
    for lineno, line in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        digest, _, name = line.partition("  ")
        digest, name = digest.strip(), name.strip()
        if len(digest) != 96 or not name:
            errors.append(f"manifest: line {lineno} is not '<sha384>  <path>': {line[:60]!r}")
            continue
        listed[name] = digest

    for required in (*REQUIRED_TOOLCHAIN_FILES, Path(__file__).name):
        if required not in listed:
            errors.append(f"manifest: required toolchain file not listed: {required}")

    for name, digest in sorted(listed.items()):
        target = toolchain / name
        if not target.is_file():
            errors.append(f"manifest: listed file missing from distribution: {name}")
        elif hashlib.sha384(target.read_bytes()).hexdigest() != digest:
            errors.append(f"manifest: hash mismatch: {name} — file differs from the signed-off inventory")
    return errors


def run_cli(script: Path, args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True,
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def allowed_pq_identifiers(register: dict) -> set[str]:
    allowed: set[str] = set()
    for profile in register["profiles"]:
        allowed.add(profile["kem_floor"])
        allowed.add(profile["sig_floor"])
        root = profile.get("release_signing_root")
        if root == "SLH-DSA":
            allowed.update({"SLH-DSA", "SLH-DSA-SHA2-128s", "SLH-DSA-SHA2-192s", "SLH-DSA-SHA2-256s"})
        elif root == "LMS":
            allowed.update({"LMS", "LMS-SHA-256/192", "LMS-SHA-256/256", "HSS/LMS"})
    # Stronger parameter sets than any floor are always acceptable.
    if "ML-KEM-768" in allowed:
        allowed.add("ML-KEM-1024")
    if "ML-DSA-65" in allowed:
        allowed.add("ML-DSA-87")
    return allowed


def check_cbom(cbom_path: Path, register: dict) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings). Unclassified cryptographic assets are
    warnings by default: a CBOM full of primitive='other' components would
    otherwise pass conformance vacuously, while the register's wrap-chain
    claim (R-14) is precisely the claim an unclassifiable component cannot
    support. --strict promotes these warnings to failures. Note the
    semantics, confirmed against QNSI's live CBOM: the CBOM classifies the
    stored asset (a vault password is 'classical'), not the envelope
    protecting it — envelope coverage is probe P-03's job, not this check's."""
    errors: list[str] = []
    warnings: list[str] = []
    cbom = json.loads(cbom_path.read_text(encoding="utf-8"))
    allowed = allowed_pq_identifiers(register)
    total = classified = 0

    for component in cbom.get("components", []):
        crypto = component.get("cryptoProperties")
        is_crypto_asset = component.get("type") == "cryptographic-asset" or crypto is not None
        if not is_crypto_asset:
            continue
        total += 1
        name = component.get("name", "")
        lowered = name.lower()
        for banned in BANNED_IDENTIFIERS:
            if banned in lowered:
                errors.append(
                    f"cbom: component '{name}' uses banned legacy identifier '{banned}' — "
                    "final FIPS nomenclature is required (PG-4)"
                )
        algo = (crypto or {}).get("algorithmProperties", {})
        primitive = algo.get("primitive", "").lower()
        if primitive in UNCLASSIFIED_PRIMITIVES:
            warnings.append(
                f"cbom: cryptographic asset '{name}' is unclassified (primitive="
                f"'{primitive or 'absent'}') — conformance cannot be assessed; the register's "
                "wrap-chain claim requires classification of wrap-chain-relevant components"
            )
            continue
        classified += 1
        if primitive in {"kem", "key-encap", "signature"}:
            identifier = algo.get("parameterSetIdentifier") or name
            if identifier not in allowed and identifier not in SYMMETRIC_AND_HASH_ALLOWED:
                errors.append(
                    f"cbom: {primitive} component '{name}' uses identifier '{identifier}' "
                    f"not permitted by any register profile (allowed: {sorted(allowed)})"
                )
    warnings.insert(0, f"cbom: {total} cryptographic asset(s), {classified} classified, "
                       f"{total - classified} unclassified")
    return errors, warnings


def check_lint(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(p for p in path.rglob("*") if p.is_file())
        elif path.is_file():
            files.append(path)
        else:
            errors.append(f"lint: path not found: {path}")
    for file in files:
        try:
            text = file.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError as exc:
            errors.append(f"lint: cannot read {file}: {exc}")
            continue
        for banned in BANNED_IDENTIFIERS:
            if banned in text:
                errors.append(
                    f"lint: banned legacy identifier '{banned}' found in {file} — "
                    "customer-facing surfaces must use final FIPS nomenclature (PG-4)"
                )
    return errors


def report(step: int, total: int, name: str, status: str, detail: str = "") -> None:
    line = f"[{step}/{total}] {name:<22} {status}"
    if detail:
        line += f"  ({detail})"
    print(line)


def main() -> int:
    parser = argparse.ArgumentParser(description="Release CI gate for the coverage register.")
    parser.add_argument("--register", type=Path, required=True)
    parser.add_argument("--schema", type=Path, default=None, help="Default: register.schema.json beside the toolchain")
    parser.add_argument("--rendered", type=Path, required=True, help="Committed rendered markdown to byte-compare")
    parser.add_argument("--template", type=Path, default=None)
    parser.add_argument("--envelope", type=Path, default=None)
    parser.add_argument("--public-key", type=Path, default=None)
    parser.add_argument("--predecessor", type=Path, default=None,
                        help="Required when the envelope is online-downgrade-signed")
    parser.add_argument("--cbom", type=Path, default=None, help="CycloneDX CBOM export to check for conformance")
    parser.add_argument("--strict", action="store_true",
                        help="Promote CBOM warnings (unclassified cryptographic assets) to failures")
    parser.add_argument("--lint-paths", type=Path, nargs="*", default=[],
                        help="Customer-facing source paths to lint for banned legacy identifiers")
    args = parser.parse_args()

    toolchain = Path(__file__).parent
    validator = toolchain / "validate_register.py"
    renderer = toolchain / "render_register.py"
    schema = args.schema or toolchain / "register.schema.json"
    template = args.template or toolchain / "matrix.template.md"

    total, step, failures = 6, 0, 0

    # 1. toolchain completeness — everything else depends on it. A published
    # set missing any toolchain file contradicts the register's promise that
    # the schema, validator, and renderer are retrievable alongside it; a
    # file differing from the manifest is a distribution whose contents were
    # never signed off.
    step += 1
    missing = [name for name in REQUIRED_TOOLCHAIN_FILES if not (toolchain / name).exists()]
    manifest_errors = check_manifest(toolchain)
    if missing or manifest_errors:
        failures += 1
        detail = f"missing beside the gate: {', '.join(missing)}" if missing \
            else f"{len(manifest_errors)} manifest error(s)"
        report(step, total, "toolchain completeness", "FAIL", detail)
        if missing:
            print("      an incomplete distribution cannot be verified — publish the full toolchain "
                  "with the signed register (one toolchain directory; version history lives in git)")
        for err in manifest_errors:
            print(f"      {err}")
    else:
        report(step, total, "toolchain completeness", "PASS",
               f"{len(REQUIRED_TOOLCHAIN_FILES)} toolchain files present; manifest verified")

    # 2. register validation
    step += 1
    code, output = run_cli(validator, [str(args.register), "--schema", str(schema)])
    if code == 0:
        report(step, total, "register validation", "PASS")
    else:
        failures += 1
        report(step, total, "register validation", "FAIL")
        print(output)

    # 3. envelope verification
    step += 1
    if args.envelope:
        env_args = [str(args.register), "--schema", str(schema), "--envelope", str(args.envelope)]
        if args.public_key:
            env_args += ["--public-key", str(args.public_key)]
        if args.predecessor:
            env_args += ["--predecessor", str(args.predecessor)]
        code, output = run_cli(validator, env_args)
        if code == 0:
            crypto = "cryptographic" if args.public_key else "structural"
            report(step, total, "signature envelope", "PASS", f"{crypto} verification")
        else:
            failures += 1
            report(step, total, "signature envelope", "FAIL")
            print(output)
    else:
        report(step, total, "signature envelope", "SKIPPED", "no --envelope supplied")

    # 4. render reproducibility
    step += 1
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    code, output = run_cli(renderer, [str(args.register), "--schema", str(schema),
                                      "--template", str(template), "--out", str(tmp_path)])
    if code != 0:
        failures += 1
        report(step, total, "render reproducibility", "FAIL", "renderer error")
        print(output)
    elif tmp_path.read_bytes() != args.rendered.read_bytes():
        failures += 1
        report(step, total, "render reproducibility", "FAIL",
               f"{args.rendered} is not byte-identical to a fresh render — hand-edit or stale rendering")
    else:
        report(step, total, "render reproducibility", "PASS", "byte-identical")
    tmp_path.unlink(missing_ok=True)

    # 5. CBOM conformance
    step += 1
    register = json.loads(args.register.read_text(encoding="utf-8"))
    if args.cbom:
        cbom_errors, cbom_warnings = check_cbom(args.cbom, register)
        real_warnings = cbom_warnings[1:]  # first entry is the summary line
        if args.strict and real_warnings:
            cbom_errors += [w.replace("cbom:", "cbom (strict):", 1) for w in real_warnings]
            real_warnings = []
        if cbom_errors:
            failures += 1
            report(step, total, "CBOM conformance", "FAIL", cbom_warnings[0].removeprefix("cbom: "))
            for err in cbom_errors:
                print(f"      {err}")
        else:
            status_detail = cbom_warnings[0].removeprefix("cbom: ")
            if real_warnings:
                status_detail += " — WARN"
            report(step, total, "CBOM conformance", "PASS", status_detail)
            for warning in real_warnings:
                print(f"      WARN  {warning}")
    else:
        report(step, total, "CBOM conformance", "SKIPPED", "no --cbom supplied")

    # 6. customer-facing string lint
    step += 1
    if args.lint_paths:
        lint_errors = check_lint(list(args.lint_paths))
        if lint_errors:
            failures += 1
            report(step, total, "string lint", "FAIL")
            for err in lint_errors:
                print(f"      {err}")
        else:
            report(step, total, "string lint", "PASS")
    else:
        report(step, total, "string lint", "SKIPPED", "no --lint-paths supplied")

    print(f"\nresult: GATE {'PASS' if failures == 0 else f'FAIL — {failures} check(s) failed'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
