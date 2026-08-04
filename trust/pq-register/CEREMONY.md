# PQ coverage-register root key ceremony (PG-8)

This is the runbook for generating the **offline-root** ML-DSA signing key and
producing the first production-signed register version. It replaces the current
`heossi-register-root-TEST-rehearsal-099` rehearsal signature.

Custody policy (from `meta.signing.key_custody` in the register): the root key is
an **offline ML-DSA key held outside CI and outside the production credential
plane**. The private key is generated on, and NEVER leaves, an air-gapped
machine. Only the public key, its fingerprint, and detached signature envelopes
leave that machine.

Roles:
- **offline-root** (this ceremony) — full-authority; signs new register versions
  and the delegation of the online-downgrade signer.
- **online-downgrade** — provisioned separately in QNSI KMS with a scoped
  entitlement; may sign only status-downgrade increments (mechanically enforced by
  `validate_register.py --predecessor`). Not part of this ceremony.

---

## 0. Prerequisites (air-gapped machine)

- Python 3.11+ and the **ceremony kit** (copied via removable media):
  `bee-pq-register.json`, `register.schema.json`, `signature-envelope.schema.json`,
  `sign_register.py`, `validate_register.py`, `mldsa.py`.
- A working ML-DSA backend. Production signing **requires liboqs** (the ACVP-proven
  native implementation) — the pure-Python fallback is refused for non-TEST key
  ids. Set up a venv *while the machine is still online*, then air-gap it:

  ```sh
  python3 -m venv ceremony-venv
  ceremony-venv/bin/python -m pip install jsonschema dilithium-py liboqs-python
  # verify the backend before going offline:
  ceremony-venv/bin/python -c "import oqs; \
    s=oqs.Signature('ML-DSA-65'); pk=s.generate_keypair(); \
    print('liboqs', oqs.oqs_version(), 'ML-DSA-65 OK')"
  ```

  (liboqs is already established in the QNSI SDK toolchain; liboqs-python 0.15.0
  bundles the same NIST-finalized ML-DSA. Use whichever liboqs your machine
  already carries as long as `oqs.Signature('ML-DSA-65')` works.)
- Verify the kit integrity against the SHA-384 manifest shipped with it before
  running anything (`shasum -a 384 -c MANIFEST.sha384`).

Use `ceremony-venv/bin/python` wherever the steps below say `python3`.

## 1. Generate the root keypair (offline)

```sh
python3 sign_register.py keygen --algorithm ML-DSA-65 --name heossi-register-root
# writes:
#   heossi-register-root.pub   (base64 public key — leaves the machine)
#   heossi-register-root.key   (base64 secret key, mode 0600 — NEVER leaves)
# prints the public-key fingerprint (sha384:...). RECORD IT.
```

Immediately back up `heossi-register-root.key` to offline media you control
(two copies, geographically separated). It is unrecoverable if lost — losing it
means a key rotation (see §5).

## 2. Sign the register (offline)

```sh
python3 sign_register.py sign bee-pq-register.json \
  --public-key heossi-register-root.pub \
  --secret-key heossi-register-root.key \
  --key-id heossi-register-root-001 \
  --signer offline-root \
  --algorithm ML-DSA-65
# writes: bee-pq-register.v<version>.sig.json (detached envelope)
# the signer VERIFIES the signature before writing it.
```

Use a stable production key id **without** the string `TEST` (e.g.
`heossi-register-root-001`). The `-001` suffix is the rotation generation.

## 3. Verify (offline, independent check)

```sh
python3 validate_register.py bee-pq-register.json \
  --envelope bee-pq-register.v<version>.sig.json \
  --public-key heossi-register-root.pub
# expect: result: VALID
#   "ML-DSA signature VERIFIED cryptographically (backend: liboqs);
#    key fingerprint matches envelope"
```

## 4. Export from the air-gapped machine (removable media)

Copy OFF the machine — never the `.key`:
- `heossi-register-root.pub`
- the recorded fingerprint (`sha384:...`)
- `bee-pq-register.v<version>.sig.json`

Hand these to the online operator. Everything needed to trust the register is
public; the private key stays offline.

## 5. What the online operator does next (not on the air-gapped machine)

1. **Anchor** the public-key fingerprint + envelope hash in the QNSI audit ledger
   (the ceremony anchor point named in `meta.signing.public_key_publication`).
2. **Publish** `heossi-register-root.pub` + fingerprint at
   `bee.heossi.com/trust/keys`, and pin the fingerprint across the three surfaces
   (QNSI audit ledger, the `heossihq` public mirror, the rendered register).
3. Commit the new `bee-pq-register.v<version>.sig.json` + updated register meta,
   re-run `pnpm trust:gate` (must PASS), and deploy.
4. Provision the **online-downgrade** key in QNSI KMS (scoped entitlement) and
   sign its delegation with the offline root at the next ceremony window.

## Rotation

Key rotation publishes a **rotation attestation signed by the outgoing root**
(bump the key-id generation `-001` → `-002`). The outgoing public key remains
published so historical envelopes stay verifiable.

---

Toolchain proven end-to-end on the **production path** (rehearsal key, real
liboqs, 2026-07-08): `keygen` → ML-DSA-65 keypair (1952-byte public key);
`sign` with a non-TEST key-id → `backend: liboqs`, detached envelope, 3309-byte
ML-DSA signature verified before writing; `validate --public-key` → `result:
VALID`, "ML-DSA signature VERIFIED cryptographically (backend: liboqs); key
fingerprint matches envelope". The commands above are exactly those.
