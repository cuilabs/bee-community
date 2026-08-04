"""Structured upgrade decision contract tests for the Python SDK."""

import io
import json
import unittest
import urllib.error
from unittest.mock import patch

from bee_sdk import Bee, BeeActionRequiredError


class UpgradeDecisionTest(unittest.TestCase):
    def test_entitlement_error_preserves_machine_readable_actions(self) -> None:
        decision = {
            "schema_version": "2026-07-31",
            "reason": "model_access_required",
            "current_plan": "bee-cell",
            "required_plan": "bee-brood",
            "actions": [
                {
                    "kind": "upgrade_plan",
                    "label": "Upgrade to bee-brood",
                    "available": True,
                    "url": "https://workspace.bee.heossi.com/account/billing",
                    "plan_id": "bee-brood",
                }
            ],
        }
        body = json.dumps({"error": {"code": "model_access_denied"}, "bee_upgrade": decision})
        response = urllib.error.HTTPError(
            "https://api.bee.heossi.com/bee/chat/completions",
            403,
            "Forbidden",
            {},
            io.BytesIO(body.encode()),
        )

        with (
            patch("urllib.request.urlopen", side_effect=response),
            self.assertRaises(BeeActionRequiredError) as raised,
        ):
            Bee(api_key="test-key", retries=0).chat("Use Bee Brood.", model="bee-brood")

        self.assertEqual(raised.exception.decision["reason"], "model_access_required")
        self.assertEqual(
            raised.exception.decision["actions"][0]["plan_id"],
            "bee-brood",
        )


if __name__ == "__main__":
    unittest.main()
