#!/usr/bin/env python3
"""Render the post-quantum coverage register into its markdown document.

Closes the claims-as-code loop: the canonical JSON register is the source
of truth; this renderer merges its data with the narrative template to
produce the published document. The renderer refuses to render a register
that fails schema or cross-reference validation, and stamps the canonical
SHA-384 hash (the ML-DSA signing preimage) into the output so every
rendering is traceable to the exact register version it came from.

Usage:
    python3 render_register.py bee-pq-register.json \
        --template matrix.template.md \
        --out bee-pq-coverage-matrix.md

Exit codes: 0 = rendered; 1 = register invalid; 2 = usage/IO error.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from validate_register import (
    canonical_bytes,
    cross_reference_errors,
    load_json,
    schema_errors,
)

KEY_HOLDER_LABELS = {
    "platform": "Platform",
    "customer": "Customer",
    "platform_or_customer": "Platform (BYOK optional → customer)",
    "none": "—",
}

STATUS_LABELS = {"covered": "**Covered**", "partial": "**Partial**", "excluded": "**Excluded**"}


def cell(text: str) -> str:
    """Escape a string for use inside a markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ").strip()


def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(cell(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def render_profiles(register: dict) -> str:
    rows = []
    for p in register["profiles"]:
        rows.append([
            p["id"],
            ", ".join(p["tiers"]),
            p["kem_floor"],
            p["sig_floor"],
            p["transport"],
            p["transport_enforcement"],
            p.get("release_signing_root", "—"),
            p.get("notes", ""),
        ])
    return table(
        ["Profile", "Bee tiers", "Key establishment floor", "Signature floor",
         "Transport", "Enforcement", "Release root", "Notes"],
        rows,
    )


def render_evidence(evidence: list[dict]) -> str:
    parts = []
    for ev in evidence:
        label = ev["label"]
        entry = f"[{label}]({ev['url']})" if ev.get("url") else label
        ships = ev.get("ships")
        if ships and ships != "live":
            entry += f" *(ships Phase {ships})*"
        parts.append(entry)
    return "; ".join(parts) if parts else "—"


def render_matrix(register: dict) -> str:
    rows = []
    for r in register["rows"]:
        mechanism = r["mechanism"]
        for q in r.get("qualifiers", []):
            mechanism += f"<br><br>*Qualifier:* {q}"
        if r.get("notes"):
            mechanism += f"<br><br>*Note:* {r['notes']}"
        effective = r["effective_phase"]
        if r.get("gate"):
            effective += f" (gate {r['gate']})"
        if r["status"] == "excluded" and r.get("closure"):
            effective = "Permanent" if r["closure"] == "permanent" else f"{r['closure']} (roadmap)"
        rows.append([
            r["id"],
            r["flow"],
            STATUS_LABELS[r["status"]],
            mechanism,
            KEY_HOLDER_LABELS[r["key_holder"]],
            r["tiers"],
            effective,
            " · ".join(r["probes"]) if r["probes"] else "—",
            render_evidence(r["evidence"]),
        ])
    return table(
        ["#", "Data flow", "Status", "Mechanism", "Key holder", "Tiers", "Effective", "Probe", "Evidence"],
        rows,
    )


def render_exclusions_summary(register: dict) -> str:
    excluded = [r for r in register["rows"] if r["status"] == "excluded"]
    boundary = [r for r in excluded if r.get("boundary_statement")]
    engineering = [r for r in excluded if not r.get("boundary_statement")]
    ids = lambda rs: ", ".join(r["id"] for r in rs)
    parts = []
    if boundary:
        parts.append(
            f"{len(boundary)} exclusions are permanent boundary statements ({ids(boundary)}): "
            "flows outside the platform's cryptographic authority."
        )
    if engineering:
        closures = sorted({r["closure"] for r in engineering if r.get("closure")})
        parts.append(
            f"{len(engineering)} are engineering exclusions with a named closure ({ids(engineering)}), "
            f"closed in Phase {', '.join(closures)}; the closing mechanism is stated in each row."
        )
    return " ".join(parts)


def render_probes(register: dict) -> str:
    rows = []
    for p in register["probes"]:
        method = p["method"]
        if p.get("detection_note"):
            method += f"<br><br>*Detection strength:* {p['detection_note']}"
        rows.append([p["id"], " · ".join(p["verifies_rows"]), method, p["cadence"]])
    return table(["Probe", "Verifies", "Method", "Cadence"], rows)


def render_gates(register: dict) -> str:
    rows = [
        [g["id"], g["description"], g["action"], g.get("automated_by") or "—"]
        for g in register["gates"]
    ]
    return table(["Gate", "What must be verified", "Owner action", "Automated by"], rows)


def render_changelog(register: dict) -> str:
    rows = []
    for entry in register["changelog"]:
        changes = "<br>".join(entry["changes"])
        if entry.get("probe_initiated"):
            changes = "*(probe-initiated)* " + changes
        rows.append([entry["version"], entry["date"], changes])
    return table(["Version", "Date", "Changes"], rows)


def build_substitutions(register: dict, digest: str) -> dict[str, str]:
    meta = register["meta"]
    disclosure = meta["disclosure_policy"]
    version = meta["version"]
    version_note = (
        "signed release" if version.startswith("1.") or int(version.split(".")[0]) >= 1
        else "pre-publication draft — becomes v1.0 when all publication gates in §12 are closed"
    )
    return {
        "{{PRODUCT}}": meta["product"],
        "{{OPERATOR}}": meta["operator"],
        "{{VERSION}}": version,
        "{{VERSION_NOTE}}": version_note,
        "{{DATE}}": meta["date"],
        "{{CLAIM}}": meta["claim"],
        "{{CANONICAL_HASH}}": f"sha384:{digest}",
        "{{PROFILES_TABLE}}": render_profiles(register),
        "{{MATRIX_TABLE}}": render_matrix(register),
        "{{EXCLUSIONS_SUMMARY}}": render_exclusions_summary(register),
        "{{PROBES_TABLE}}": render_probes(register),
        "{{GATES_TABLE}}": render_gates(register),
        "{{CHANGELOG_TABLE}}": render_changelog(register),
        "{{SIGNING_CANONICALIZATION}}": meta["signing"]["canonicalization"],
        "{{SIGNING_CUSTODY}}": meta["signing"]["key_custody"],
        "{{SIGNING_ENVELOPE}}": meta["signing"]["envelope"],
        "{{KEY_PUBLICATION}}": meta["signing"]["public_key_publication"],
        "{{CHAIN_POLICY}}": meta.get("chain_policy", "The hash chain begins at the first canonical version."),
        "{{DOWNGRADE_TRIGGER}}": register["probe_semantics"]["downgrade_trigger"],
        "{{INCONCLUSIVE_HANDLING}}": register["probe_semantics"]["inconclusive_handling"],
        "{{RESTORATION}}": register["probe_semantics"]["restoration"],
        "{{DISCLOSURE_INTERNAL}}": disclosure["internal_downgrade"],
        "{{DISCLOSURE_HOURS}}": str(disclosure["public_publication_max_hours"]),
        "{{DISCLOSURE_EXCEPTION}}": disclosure["exploitation_exception"],
        "{{LEGAL_SCOPE}}": meta["legal_scope"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the coverage register into markdown.")
    parser.add_argument("register", type=Path, help="Path to the register JSON instance")
    parser.add_argument("--schema", type=Path, default=Path(__file__).with_name("register.schema.json"))
    parser.add_argument("--template", type=Path, default=Path(__file__).with_name("matrix.template.md"))
    parser.add_argument("--out", type=Path, required=True, help="Output markdown path")
    args = parser.parse_args()

    register = load_json(args.register)
    schema = load_json(args.schema)

    errors = schema_errors(register, schema) + cross_reference_errors(register)
    if errors:
        for err in errors:
            print(f"FAIL  {err}", file=sys.stderr)
        print(f"refusing to render: register is INVALID ({len(errors)} error(s))", file=sys.stderr)
        return 1

    try:
        template = args.template.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"error: template not found: {args.template}", file=sys.stderr)
        return 2

    digest = hashlib.sha384(canonical_bytes(register)).hexdigest()
    document = template
    for placeholder, value in build_substitutions(register, digest).items():
        document = document.replace(placeholder, value)

    unresolved = [line for line in document.splitlines() if "{{" in line]
    if unresolved:
        for line in unresolved:
            print(f"FAIL  unresolved placeholder: {line.strip()}", file=sys.stderr)
        return 1

    args.out.write_text(document, encoding="utf-8")
    print(f"rendered: {args.out}")
    print(f"register version: {register['meta']['version']}  canonical hash: sha384:{digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
