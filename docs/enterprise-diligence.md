# Bee enterprise diligence index

This index is the public starting point for evaluating Bee without access to
HEOSSI's proprietary serving and orchestration implementation. It separates
inspectable public evidence from production facts that require customer-scoped
qualification.

## Public evidence map

| Question | Public evidence | Boundary |
| --- | --- | --- |
| What crosses the customer/service boundary? | [Reference architecture](./architecture.md) and [governed scenarios](./scenarios/README.md) | Diagrams describe the public contract, not every private service component |
| What API behavior is contracted? | [`api/openapi.json`](../api/openapi.json) and [`api/postman.json`](../api/postman.json) | Production availability remains observable at the live API and status page |
| What client code can be inspected? | [TypeScript and Python SDKs](../sdks/) plus [examples](../examples/) | Bee Code, hosted orchestration, and model-engine implementations remain proprietary |
| How does MCP connect? | [MCP catalog and configurations](../mcp/) | Authentication, tenant, entitlement, and usage policy are enforced by the hosted gateway |
| What post-quantum claims are released? | [Signed PQ coverage register](../trust/pq-register/) | Coverage is limited to the register's named paths and must not be generalized |
| How is the export traced and checked? | [`MANIFEST.json`](../MANIFEST.json), [`SHA256SUMS`](../SHA256SUMS), and [`SBOM.spdx.json`](../SBOM.spdx.json) | The SBOM is package-level and does not describe private deployment infrastructure |
| How are vulnerabilities reported? | [`SECURITY.md`](../SECURITY.md) | Customer incident procedures and contractual notification terms are engagement-specific |
| What is live now? | [Status](https://bee.heossi.com/status), [changelog](https://bee.heossi.com/changelog), and [roadmap](https://bee.heossi.com/roadmap) | Roadmap statements are not present-tense availability claims |

## Evidence levels

| Level | Meaning |
| --- | --- |
| Public source | An implementation, contract, or document is present in this export |
| Reproducible artifact | A checksum, manifest, signed register, or runnable verification path is published |
| Live service observation | A public endpoint or registry can be queried at evaluation time |
| Customer-qualified control | Deployment, tenancy, region, custody, telemetry, support, or assurance is fixed for a named engagement |

Source presence is not production proof. A package release is not evidence that
every hosted capability is enabled. A diagram is not a certification. Customer
assurance must use the applicable Order Form, deployment manifest, data terms,
and evidence package alongside these public materials.

## Suggested review sequence

1. Confirm the [public/proprietary boundary](../README.md#public-and-proprietary-boundary).
2. Review the [system boundary](./architecture.md#system-boundary) and relevant scenario.
3. Inspect the API or package contract used by the intended integration.
4. Verify `SHA256SUMS`, the export manifest, and any applicable signed PQ register artifact.
5. Check current status and changelog entries.
6. Record the controls that still require customer-specific qualification.
