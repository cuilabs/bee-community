from datetime import datetime, timedelta, timezone
import unittest

from bee_sdk.quantum_local import execute_byopa_direct, quantum_local_select


class Adapter:
    def quote(self, _request):
        return {"cost_minor": 1, "currency": "USD", "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()}

    def run(self, request, _quote):
        return {"provider_job_id": "job", "backend": request["backend"], "counts": {"00": request["shots"]}, "billed_cost_minor": 1}


class QuantumLocalTests(unittest.TestCase):
    def test_local_is_deterministic_and_customer_cpu(self):
        first = quantum_local_select(["a", "b"], [0.0, 1.0], shots=100, seed=7)
        second = quantum_local_select(["a", "b"], [0.0, 1.0], shots=100, seed=7)
        self.assertEqual(first, second)
        self.assertEqual(first.backend, "customer_cpu")
        self.assertEqual(first.qubits, 1)
        self.assertAlmostEqual(sum(value * value for value in first.amplitudes), 1.0)

    def test_rejects_nonfinite_score(self):
        with self.assertRaises(ValueError): quantum_local_select(["a"], [float("nan")])

    def test_rejects_boolean_or_fractional_shots(self):
        for value in (True, 1.5):
            with self.assertRaises(ValueError): quantum_local_select(["a"], [1.0], shots=value)  # type: ignore[arg-type]

    def test_byopa_validates_quote_cap(self):
        adapter = Adapter()
        adapter.quote = lambda _request: {"cost_minor": 2, "currency": "USD", "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()}
        with self.assertRaises(ValueError): execute_byopa_direct({"circuit": "x", "shots": 1, "backend": "qpu", "max_cost_minor": 1, "currency": "USD"}, adapter)

    def test_byopa_accepts_exact_bounded_result(self):
        result = execute_byopa_direct({"circuit": "x", "shots": 2, "backend": "qpu", "max_cost_minor": 1, "currency": "USD"}, Adapter())
        self.assertEqual(result["counts"], {"00": 2})


if __name__ == "__main__": unittest.main()
