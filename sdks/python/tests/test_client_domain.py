"""Domain-routing contract tests for the public Python client."""

import unittest
from typing import Any

from bee_sdk import Bee


class RecordingBee(Bee):
    def __init__(self) -> None:
        super().__init__(base_url="https://api.bee.heossi.com/bee", api_key="test-key")
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def _request(  # type: ignore[override]
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        *,
        retries: int | None = None,
    ) -> dict[str, Any]:
        del headers, retries
        self.calls.append((method, path, body))
        return {
            "id": "chatcmpl-test",
            "model": "bee-cell",
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {},
            "bee_domain_intelligence": {
                "version": "bsis-signals-v1",
                "primary_domain": "cryptography_pqc",
                "perspectives": ["cryptography_pqc"],
                "serving": "baseline_specialist_synthesis",
                "evidence_policy": "live_sources_recommended",
                "recommended_model": None,
                "notice": "The specialist adapter is not active.",
            },
        }


class ClientDomainTest(unittest.TestCase):
    def test_explicit_domain_is_sent_with_the_chat_completion(self) -> None:
        bee = RecordingBee()

        self.assertEqual(
            bee.chat("Assess this migration.", domain="cryptography_pqc"),
            "ok",
        )

        self.assertEqual(len(bee.calls), 1)
        method, path, body = bee.calls[0]
        self.assertEqual((method, path), ("POST", "/chat/completions"))
        self.assertEqual(body["domain"] if body else None, "cryptography_pqc")

    def test_omitted_domain_uses_governed_automatic_routing(self) -> None:
        bee = RecordingBee()

        self.assertEqual(bee.chat("Classify and answer this."), "ok")

        body = bee.calls[0][2]
        self.assertNotIn("domain", body or {})

    def test_response_exposes_the_auditable_domain_decision(self) -> None:
        response = RecordingBee().chat_messages(
            [],
            domain="cryptography_pqc",
        )
        self.assertEqual(
            response.domain_intelligence["primary_domain"]
            if response.domain_intelligence
            else None,
            "cryptography_pqc",
        )

    def test_computer_use_host_report_validation_uses_gateway_route(self) -> None:
        bee = RecordingBee()
        out = bee.validate_computer_use_host_report(
            {
                "protocol": "bee.computer.v1",
                "host_id": "host-1",
                "host_type": "macos_desktop",
                "version": "1.0.0",
                "capabilities": {
                    "screen_observation": {"state": "supported", "reason": None},
                    "accessibility_tree": {"state": "permission_required", "reason": "Accessibility"},
                    "pointer_input": {"state": "permission_required", "reason": "Accessibility"},
                    "keyboard_input": {"state": "permission_required", "reason": "Accessibility"},
                    "browser_navigation": {"state": "unsupported", "reason": "not browser"},
                },
                "evidence": {"checked_at": "2026-09-01T00:00:00.000Z", "checker": "test"},
            }
        )

        method, path, body = bee.calls[-1]
        self.assertEqual((method, path), ("POST", "/computer/v1/host-reports"))
        self.assertEqual(body["host"]["host_id"] if body else None, "host-1")
        self.assertEqual(out["id"], "chatcmpl-test")


if __name__ == "__main__":
    unittest.main()
