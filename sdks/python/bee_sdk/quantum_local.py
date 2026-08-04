"""Customer-local statevector selection and BYOPA-direct validation (stdlib only)."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass(frozen=True)
class QuantumLocalResult:
    selected_index: int
    selected: str
    probabilities: list[float]
    amplitudes: list[float]
    qubits: int
    counts: dict[str, int]
    shots: int
    backend: str


def _valid_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def quantum_local_select(
    candidates: list[str], scores: list[float], shots: int = 2_000, seed: int = 0xBEE
) -> QuantumLocalResult:
    if not 1 <= len(candidates) <= 256 or len(scores) != len(candidates):
        raise ValueError("candidates and scores must have the same length from 1 to 256")
    if any(not value or len(value) > 256_000 for value in candidates):
        raise ValueError("invalid candidate")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in scores):
        raise ValueError("scores must be finite numbers")
    if not _valid_int(shots) or not 1 <= shots <= 100_000 or not _valid_int(seed):
        raise ValueError("shots or seed out of range")
    high = max(scores)
    weights = [math.exp(score - high) for score in scores]
    total = sum(weights)
    probabilities = [value / total for value in weights]
    qubits = max(1, math.ceil(math.log2(len(candidates))))
    amplitudes = [
        math.sqrt(probabilities[index]) if index < len(probabilities) else 0.0
        for index in range(2**qubits)
    ]
    rng = random.Random(seed)
    counts: dict[str, int] = {}
    for _ in range(shots):
        sample = rng.random()
        cumulative = 0.0
        index = len(probabilities) - 1
        for candidate, probability in enumerate(probabilities):
            cumulative += probability
            if sample < cumulative:
                index = candidate
                break
        counts[str(index)] = counts.get(str(index), 0) + 1
    selected_index = int(max(counts, key=counts.get))  # type: ignore[arg-type]
    return QuantumLocalResult(
        selected_index,
        candidates[selected_index],
        probabilities,
        amplitudes,
        qubits,
        counts,
        shots,
        "customer_cpu",
    )


class ByopaDirectAdapter(Protocol):
    def quote(self, request: dict) -> dict: ...
    def run(self, request: dict, quote: dict) -> dict: ...


def execute_byopa_direct(request: dict, adapter: ByopaDirectAdapter) -> dict:
    circuit, shots = request.get("circuit"), request.get("shots")
    backend, cap, currency = request.get("backend"), request.get("max_cost_minor"), request.get("currency")
    if not isinstance(circuit, str) or not circuit or len(circuit) > 1_000_000:
        raise ValueError("invalid circuit")
    if not _valid_int(shots) or not 1 <= shots <= 100_000:
        raise ValueError("invalid shots")
    if not isinstance(backend, str) or not backend or len(backend) > 200:
        raise ValueError("invalid backend")
    if not _valid_int(cap) or cap < 0 or not isinstance(currency, str) or len(currency) != 3 or not currency.isupper():
        raise ValueError("invalid cost cap or currency")
    quote = adapter.quote(request)
    expires = quote.get("expires_at")
    try:
        expiry = datetime.fromisoformat(str(expires).replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("provider returned invalid quote") from error
    if expiry.tzinfo is None:
        raise ValueError("provider returned invalid quote")
    cost = quote.get("cost_minor")
    if not _valid_int(cost) or cost < 0 or cost > cap or quote.get("currency") != currency or expiry <= datetime.now(timezone.utc):
        raise ValueError("provider returned invalid quote")
    result = adapter.run(request, quote)
    counts = result.get("counts")
    if (
        not isinstance(result.get("provider_job_id"), str)
        or not result["provider_job_id"]
        or result.get("backend") != backend
        or not isinstance(counts, dict)
        or not counts
        or any(
            not isinstance(key, str)
            or not 1 <= len(key) <= 64
            or set(key) - {"0", "1"}
            or not _valid_int(value)
            or value < 0
            for key, value in counts.items()
        )
        or sum(counts.values()) != shots
    ):
        raise ValueError("provider returned invalid result")
    billed = result.get("billed_cost_minor")
    if billed is not None and (not _valid_int(billed) or billed < 0 or billed > cost or billed > cap):
        raise ValueError("provider returned invalid bill")
    return result
