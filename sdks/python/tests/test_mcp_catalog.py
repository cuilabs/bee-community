"""Contract tests for the public MCP catalog used by registries and Glama."""

import unittest

from bee_sdk.mcp import DOMAINS, RESOURCE_TEMPLATES, RESOURCES, TOOLS

EXPECTED_TOOLS = [
    "bee_chat",
    "bee_code",
    "bee_security",
    "bee_research",
    "bee_verify_provenance",
    "bee_usage",
    "bee_documents_search",
    "bee_documents_add",
    "bee_memory_search",
    "bee_memory_add",
    "bee_quantum_reasoning_run",
    "bee_quantum_reasoning_jobs",
    "bee_quantum_reasoning_get",
    "bee_quantum_reasoning_remove",
]

EXPECTED_MCP_DOMAINS = [
    "general",
    "programming",
    "ai",
    "cybersecurity",
    "cryptography_pqc",
    "quantum",
    "fintech",
    "blockchain",
    "infrastructure",
    "research",
    "business",
]


class MCPCatalogTest(unittest.TestCase):
    def test_domain_catalog_matches_the_hosted_curated_surface(self) -> None:
        self.assertEqual(DOMAINS, EXPECTED_MCP_DOMAINS)
        self.assertEqual(TOOLS[0]["inputSchema"]["properties"]["domain"]["enum"], EXPECTED_MCP_DOMAINS)

    def test_exact_tool_catalog_and_behavioral_annotations(self) -> None:
        self.assertEqual([tool["name"] for tool in TOOLS], EXPECTED_TOOLS)
        read_only = 0
        writes = 0
        for tool in TOOLS:
            self.assertTrue(tool["title"])
            self.assertGreaterEqual(len(tool["description"]), 80)
            annotations = tool["annotations"]
            self.assertEqual(annotations["title"], tool["title"])
            for hint in (
                "readOnlyHint",
                "destructiveHint",
                "idempotentHint",
                "openWorldHint",
            ):
                self.assertIsInstance(annotations[hint], bool)
            read_only += annotations["readOnlyHint"] is True
            writes += annotations["readOnlyHint"] is False
        self.assertEqual(read_only, 10)
        self.assertEqual(writes, 4)

    def test_resources_are_exact_and_tenant_data_is_described(self) -> None:
        self.assertEqual(
            [resource["uri"] for resource in RESOURCES],
            ["bee://status", "bee://domains", "bee://documents", "bee://memory"],
        )
        self.assertEqual(
            [template["uriTemplate"] for template in RESOURCE_TEMPLATES],
            ["bee://documents/{source}"],
        )


if __name__ == "__main__":
    unittest.main()
