# Bee post-quantum coverage matrix

**Document class:** Public claims register · Trust & Evidence · self-verifying control plane
**Applies to:** {{PRODUCT}}, operated by {{OPERATOR}}
**Version:** {{VERSION}} ({{VERSION_NOTE}})
**Date:** {{DATE}}
**Canonical register:** this document is a rendering of the signed machine-readable register (canonical hash `{{CANONICAL_HASH}}`) — it is generated, never hand-edited. Verify the register with the published validator before trusting this rendering.

---

## 1. The claim

> **{{CLAIM}}**

This register exists so that the claim above can be audited rather than trusted — and so that it *cannot silently rot*: every Covered row is bound to a scheduled production probe (§9) whose failure automatically downgrades the row and re-signs the register. Every data flow in the Bee platform is enumerated in §5 with one of three statuses — **Covered**, **Partial**, or **Excluded** — together with the protecting mechanism, the key holder, the tiers it applies to, its probe, and a link to live evidence. Exclusions are stated as plainly as coverage.

What the claim deliberately does **not** say:

- It does not say "quantum LLM." Bee's explicit, add-on quantum-compute path is separate from model inference and is not part of this security claim.
- It does not say "everything, everywhere." §6 lists the flows that are out of scope today, why, and — where applicable — the phase that closes them.
- It does not assert the post-quantum posture of third-party subprocessors or of customer-controlled devices.

## 2. Definitions

**Post-quantum protected (transport):** the connection negotiates a hybrid key exchange combining X25519 with ML-KEM-768 (FIPS 203) or stronger, such that recorded traffic is not decryptable by a future cryptographically relevant quantum computer (CRQC) even if the classical component fails. Hybrid negotiation requires client-side support; the enforcement column of §3 states, per profile, whether classical fallback is permitted (`prefer`) or rejected (`require`).

**Post-quantum protected (at rest):** the data is encrypted with AES-256-GCM under a per-object data-encryption key (DEK), and every key that protects that DEK — up to and including the tenant key-encryption key (KEK) held in QNSI KMS — is wrapped using ML-KEM (FIPS 203). No RSA or classical elliptic-curve key exchange appears anywhere in the wrap chain. AES-256 itself retains 128-bit effective security against Grover-type attacks and is the CNSA 2.0 symmetric baseline.

**Post-quantum provenance:** the record (audit event, inference receipt, migration attestation) carries an ML-DSA (FIPS 204) signature and is anchored into a Merkle-tree ledger whose checkpoints are ML-DSA-signed. Receipt content commitments are salted per-tenant HMACs, never bare hashes.

**Post-quantum integrity:** the artifact (model weights, LoRA adapter, system prompt, MCP manifest, release binary) is ML-DSA-signed and verified before load or install; long-horizon release roots use SLH-DSA (FIPS 205) on commercial profiles and the SP 800-208 stateful hash-based track (LMS) on the government profile.

**Key holder — platform:** HEOSSI operates the key in QNSI KMS under Bee's platform credential, scoped per tenant.
**Key holder — customer:** the customer operates the key in their own QNSI tenant (BYOK). While Bee serves the tenant it holds a customer-revocable wrap/unwrap entitlement — inference requires decryption — and the guarantee is that the customer can revoke or destroy the key unilaterally at any moment, after which the data is unreadable to HEOSSI, including support and backups, with no recovery path.

**Probe:** a scheduled or event-driven production check, defined in §9, that verifies a row's mechanism against deployed reality rather than against documentation. A failed probe auto-downgrades its rows; a probe that cannot measure reports `inconclusive`, which pages the operator and never downgrades.

**Crypto-agility RTO:** the measured time to re-wrap the entire estate of tenant key material under a replacement KEM following a deprecation or break of a deployed algorithm. Because the quantum-dependent operation exists only on ~32-byte key wraps — never on the data itself — algorithm replacement is a metadata-scale operation using the same machinery as BYOK migration. See §10.

**CRQC threat model:** harvest-now-decrypt-later (HNDL) adversaries recording ciphertext today for future decryption. LLM conversation logs, memory, and retrieval corpora are long-lived, high-sensitivity data and are treated as priority HNDL targets throughout this register.

## 3. Cryptographic profiles by tier

Crypto posture escalates with the Bee tier and is enforced by the QNSI policy engine at key-creation time — a request below the tier's floor is rejected by the platform, not discouraged by documentation.

{{PROFILES_TABLE}}

Parameter-set note: ML-KEM-768 / ML-DSA-65 are appropriate civilian defaults (aligned with, e.g., UK NCSC guidance) but are **not** CNSA 2.0 compliant. CNSA 2.0 names ML-KEM-1024 and ML-DSA-87 specifically. Buyers with NSS-adjacent obligations must use the government profile.

Naming note: all public identifiers use final FIPS nomenclature (ML-KEM-768, not "kyber-768"). FIPS 203 conformance — including final parameter encoding and OIDs — is asserted only after publication gate PG-4 is closed; round-3 CRYSTALS-Kyber equivalence is not treated as compliance. Deployed algorithm reality is diffed against this section on every release via the published CBOM (probe P-07).

## 4. Reading the matrix

- **Covered** — the mechanism is live for the stated tiers, evidence is linked, and the row is bound to a production probe.
- **Partial** — a defined subset is protected; the unprotected remainder and its closure path are stated in the same row. Partial is a precise engineering status, not a hedge. Probes for Partial rows activate when the row's gate closes.
- **Excluded** — outside the claim. The reason is stated; where a closure exists on the roadmap, the phase is named. Permanent exclusions are boundary statements — honesty about the boundary is the point of this register.
- **Effective** — the build phase (A–D, per the integration plan) at which the row's status holds, with the row's publication gate where one applies. Later-phase rows are roadmap and are labeled as such wherever this claim is marketed.
- **Probe** — the P-ID from §9 continuously verifying the row. A row cannot carry Covered status without a probe.
- **Qualifiers** — honest constraints on a status, rendered with the row itself, never footnoted away. A qualifier bounds the claim; it does not soften it.

## 5. Coverage matrix

{{MATRIX_TABLE}}

## 6. Summary of exclusions

{{EXCLUSIONS_SUMMARY}} No other exclusions exist. If a reviewer identifies a data flow not enumerated here, it is treated as a defect in this register — report it to bee-security@heossi.com (RFC 9116: /.well-known/security.txt) and it will be added with an honest status.

## 7. Independent verification

This register maps to the QNSI vendor test for post-quantum claims (qnsi.heossi.com/pqc-theatre). Bee answers it on the record:

1. **Which algorithms and parameter sets, exactly?** §3 of this register, per tier — final FIPS nomenclature, with the CNSA 2.0 parameter distinction stated rather than blurred. Full algorithm inventory: qnsi.heossi.com/algorithms. Deployed reality is diffable against the claim via the published CycloneDX CBOM on every release.
2. **Can the cryptography be verified without trusting the vendor?** Yes, at four depths: NIST ACVP conformance vectors (qnsi.heossi.com/verify/conformance); the live public PQC sandbox (fresh operations per request, no canned output); the PQC-TLS canary with published negotiated-group telemetry; and — from Phase B — the public receipt-verification endpoint where anyone can validate a Bee inference receipt's ML-DSA signature and Merkle inclusion with no Bee account. The probe implementations in §9 are published, so a customer can run the same checks Bee runs against its own production — including the wrap-chain audit against their own data export, exhaustively.
3. **Where are the keys and who can use them?** §2 key-holder definitions, the row-by-row key-holder column, the per-tenant coverage endpoint (§11.1) showing each customer their own key custody in real time, and the BYOK path under which the customer can unilaterally revoke or destroy their key at any moment, rendering their data unreadable to HEOSSI with no recovery path.
4. **What is not covered?** §5 and §6. The exclusions are published in the same table as the coverage, at the same level of detail, including the plaintext-in-memory reality every production LLM shares.

Performance transparency: post-quantum overhead per completion is measured continuously by probe P-05 and published as rolling percentiles in the QNSI benchmarks format — a rounding error against multi-second inference, and stated so buyers do not have to take it on faith.

## 8. Register operations — claims as code

This document is a **rendering**, not the source of truth.

- **Canonical form:** the machine-readable register file (published schema per §11.4) in which every section of this document that carries a table is structured data: rows, profiles, probes, gates, changelog, governance. The file is ML-DSA-signed and carries the hash of its predecessor.
- **Canonicalization and signing:** {{SIGNING_CANONICALIZATION}}
- **Detached signature envelope:** {{SIGNING_ENVELOPE}}
- **Verification key publication and pinning:** {{KEY_PUBLICATION}}
- **Key custody:** {{SIGNING_CUSTODY}}
- **Rendered surfaces:** this document, the bee.heossi.com/trust web page, and the security-review packet are all generated from the canonical file by the published renderer. None is hand-edited; divergence between surfaces is therefore structurally impossible. The renderer refuses to render a register that fails validation.
- **CI enforcement:** the Bee release pipeline diffs each release against the register. A change that alters cryptographic behavior — algorithm identifiers, wrap-chain structure, signing keys, transport groups — without a corresponding signed register change **fails the build**. The register is a gate, not a bystander.
- **Public availability:** the current signed canonical file, the schema, the validator, and the renderer are retrievable at the coverage endpoint (§11.1), so third parties verify the signature over the canonical hash and consume the register programmatically rather than scraping prose.

## 9. Continuous verification — probes and auto-downgrade

### 9.1 Probe specifications

{{PROBES_TABLE}}

Probe implementations are published alongside the register so customers and auditors can execute the identical checks independently.

### 9.2 Probe semantics

- **States:** pass · fail · inconclusive.
- **Downgrade trigger:** {{DOWNGRADE_TRIGGER}}
- **Inconclusive handling:** {{INCONCLUSIVE_HANDLING}}
- **Restoration:** {{RESTORATION}}

The register therefore tracks production reality mechanically — it cannot overstate coverage through neglect, and the human commitment in §13 becomes the fallback, not the mechanism.

## 10. Crypto-agility — the re-wrap RTO

Post-quantum algorithms are themselves young; a credible register must answer "what if ML-KEM falls?" with a benchmark, not reassurance.

Because no data is ever encrypted directly under a quantum-dependent algorithm — only ~32-byte DEK wraps are — replacing a deprecated KEM across the entire estate is a re-wrap of key material using the same machinery as BYOK migration: unwrap under the outgoing KEK, re-wrap under a replacement-algorithm KEK, at metadata scale, with the data untouched.

- **Commitment:** full-estate re-wrap RTO target of ≤ 24 hours from decision to completion, per deployed region.
- **Evidence:** an annual re-wrap drill executed against production-scale key volume on a canary population; the measured figure is published in the QNSI benchmarks format and referenced here after the first drill. The published number is always a measured drill result, never a projection.
- **Algorithm diversity:** QNSI's multi-family catalog (lattice, code-based, hash-based) means the replacement target for a lattice deprecation already exists in the platform, and the government profile's LMS signing track is deliberately non-lattice.

## 11. Capability surfaces

### 11.1 Per-tenant coverage endpoint

From Phase C: `GET /v1/trust/coverage` returns the current signed canonical register (public, unauthenticated). `GET /v1/trust/coverage/tenant` (authenticated) returns the register **instantiated for the calling tenant**: their crypto profile and enforced parameter floor, their key holder per row (platform KEK ID or their own QNSI KEK ID), last KEK rotation timestamp, live receipt/anchoring statistics against SLO, probe status summary, and — where applicable — their BYOK migration attestation. The same view renders as a workspace dashboard panel and exports as the tenant's evidence pack.

### 11.2 Policy-versioned receipts

Every inference receipt embeds the canonical register version in force at issue time. A receipt therefore proves not only *what* was produced and *when*, but *which published security regime governed it* — auditable retroactively against this register's signed version history even years later.

### 11.3 Compliance framework cross-mapping

Each canonical register row carries a controls field mapping the mechanism to the control families it evidences — SOC 2, ISO/IEC 27001:2022 Annex A, PDPA, and the MAS TRM guidelines — inheriting QNSI's published seven-framework compliance mapping (qnsi.heossi.com/security/compliance). The register thereby doubles as the cryptography-control evidence index for Bee's own ISO 27001 track and planned SOC 2 Type II.

### 11.4 Open specification

The register's schema is published as an open specification — a reporting format any AI vendor can complete for their own product — released alongside the QNSI vendor test at v1.0. Bee's register is the reference implementation. The specification requires published, third-party-executable probes for every covered row: a register cannot be satisfied on paper. Vendors who adopt it expose their exclusions at the same resolution as ours; vendors who decline concede the verifiability ground.

## 12. Publication gates ({{VERSION}} → v1.0)

This register is published as v1.0 — and the §1 claim is marketed — only when every gate below is closed. Each closure is recorded in the audit ledger.

{{GATES_TABLE}}

## 13. Governance and change control

- **Disclosure policy:** internal downgrade is {{DISCLOSURE_INTERNAL}}; the public register is updated within {{DISCLOSURE_HOURS}} hours. {{DISCLOSURE_EXCEPTION}}
- **Legal scope:** {{LEGAL_SCOPE}}
- **Chain policy:** {{CHAIN_POLICY}}
- The canonical register file is the versioned artifact; each version carries an ML-DSA signature and the hash of its predecessor, forming a verifiable history anchored in the QNSI audit ledger.
- Any status change, algorithm change, key-holder change, probe change, or controls-mapping change increments the version and is announced in the Bee changelog (bee.heossi.com/changelog). Auto-downgrades are version increments like any other, flagged as probe-initiated.
- The register is reviewed at every phase boundary (A→B→C→D) and at minimum quarterly.
- Discrepancy handling: probe-detectable divergence downgrades automatically per §9.2. For divergence outside probe coverage, a Covered row is downgraded within 5 business days of confirmation — the register tracks reality, never the other way around.

### Register changelog

{{CHANGELOG_TABLE}}

---

*Operated by {{OPERATOR}}. Related evidence surfaces: bee.heossi.com/trust · bee.heossi.com/quantum · qnsi.heossi.com/security. Security contact: bee-security@heossi.com. Rendered from register version {{VERSION}}, canonical hash `{{CANONICAL_HASH}}`.*
