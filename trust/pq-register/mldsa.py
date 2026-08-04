#!/usr/bin/env python3
"""ML-DSA (FIPS 204) backend resolution for the coverage-register toolchain.

Backend order:
  1. liboqs (python bindings, C implementation) — preferred for the
     production key ceremony.
  2. dilithium-py — pure-Python FIPS 204 implementation; always available
     via pip, suitable for third-party verification and rehearsals.

Both tools (sign_register.py, validate_register.py --public-key) resolve
through this module so signing and verification are guaranteed to agree
on algorithm parameters regardless of which backend is present.
"""

from __future__ import annotations


class MLDSABackend:
    def __init__(self, algorithm: str, name: str, keygen, sign, verify):
        self.algorithm = algorithm
        self.name = name
        self.keygen = keygen      # () -> (public_key: bytes, secret_key: bytes)
        self.sign = sign          # (secret_key: bytes, message: bytes) -> bytes
        self.verify = verify      # (public_key: bytes, message: bytes, signature: bytes) -> bool


_OQS_NAMES = {"ML-DSA-65": "ML-DSA-65", "ML-DSA-87": "ML-DSA-87"}


def _try_liboqs(algorithm: str) -> MLDSABackend | None:
    try:
        import oqs  # type: ignore
    except ImportError:
        return None

    oqs_name = _OQS_NAMES[algorithm]

    def keygen():
        with oqs.Signature(oqs_name) as signer:
            public_key = signer.generate_keypair()
            secret_key = signer.export_secret_key()
        return public_key, secret_key

    def sign(secret_key: bytes, message: bytes) -> bytes:
        with oqs.Signature(oqs_name, secret_key) as signer:
            return signer.sign(message)

    def verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
        with oqs.Signature(oqs_name) as verifier:
            return verifier.verify(message, signature, public_key)

    return MLDSABackend(algorithm, "liboqs", keygen, sign, verify)


def _try_dilithium_py(algorithm: str) -> MLDSABackend | None:
    try:
        from dilithium_py.ml_dsa import ML_DSA_65, ML_DSA_87  # type: ignore
    except ImportError:
        return None

    impl = {"ML-DSA-65": ML_DSA_65, "ML-DSA-87": ML_DSA_87}[algorithm]
    return MLDSABackend(
        algorithm,
        "dilithium-py",
        keygen=lambda: impl.keygen(),
        sign=lambda sk, msg: impl.sign(sk, msg),
        verify=lambda pk, msg, sig: impl.verify(pk, msg, sig),
    )


def resolve(algorithm: str) -> MLDSABackend:
    """Return the first available backend for the given FIPS 204 parameter set."""
    if algorithm not in _OQS_NAMES:
        raise ValueError(f"unsupported algorithm: {algorithm} (expected ML-DSA-65 or ML-DSA-87)")
    backend = _try_liboqs(algorithm) or _try_dilithium_py(algorithm)
    if backend is None:
        raise RuntimeError(
            "no ML-DSA backend available: install liboqs-python or `pip install dilithium-py`"
        )
    return backend
