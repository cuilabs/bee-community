"""Public types for the Bee SDK.

Mirrors the JSON shape of the Bee API. Kept as standard-library dataclasses and
typed dictionaries-no pydantic dependency-so the SDK stays lightweight.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypedDict


class UpgradeAction(TypedDict, total=False):
    kind: Literal[
        "upgrade_plan",
        "enable_usage_credits",
        "add_credits",
        "manage_spend_cap",
        "purchase_addon",
        "compact_context",
        "new_conversation",
        "retry_later",
        "contact_sales",
    ]
    label: str
    available: bool
    url: str | None
    plan_id: str


class UpgradeDecision(TypedDict, total=False):
    schema_version: Literal["2026-07-31"]
    reason: str
    current_plan: str
    required_plan: str | None
    requested_model: str
    requested_domain: str
    requested_feature: str
    binding_limit: dict[str, object]
    actions: list[UpgradeAction]


QuantumReasoningModel = Literal["bee-hive", "bee-swarm"]
QuantumProductId = Literal[
    "local_simulator",
    "simulation_cloud",
    "managed_qpu",
    "byopa_direct",
    "byopa_managed",
]
QuantumReasoningJobStatus = Literal[
    "queued",
    "generating_candidates",
    "scoring",
    "selecting",
    "awaiting_qpu",
    "completed",
    "classical_fallback",
    "failed",
    "cancelled",
]
QuantumReasoningOutcomeState = Literal[
    "not_started",
    "in_progress",
    "committed",
    "outcome_unknown",
    "reconciled",
]
QuantumReasoningFallbackReason = Literal["selector_unreachable", "invalid_selection"]
QuantumReasoningRealRequestStatus = Literal[
    "not_requested",
    "reserved",
    "executed",
    "provider_used_simulator",
    "quantum_not_enabled",
    "quantum_allowance_exhausted",
    "released_after_failure",
]


class QuantumReasoningCandidate(TypedDict):
    index: int
    content: str
    score: float


class QuantumReasoningJob(TypedDict, total=False):
    id: str
    product: QuantumProductId
    status: QuantumReasoningJobStatus
    model: QuantumReasoningModel
    scoring_method: str
    requested_real: bool
    prompt: str
    candidates: list[QuantumReasoningCandidate]
    selected_index: int
    result: str
    selector_backend: str
    selector_confidence: float
    used_real_qubits: bool
    quoted_credits: float | None
    fallback_reason: QuantumReasoningFallbackReason | None
    real_request_status: QuantumReasoningRealRequestStatus
    usage: dict[str, int | float]
    inference_receipt_id: str | None
    attempt_count: int
    max_attempts: int
    next_attempt_at: str | None
    outcome_state: QuantumReasoningOutcomeState
    error: dict[str, str] | None
    workspace_id: str | None
    created_at: str
    updated_at: str
    completed_at: str | None


class QuantumReasoningJobPage(TypedDict, total=False):
    jobs: list[QuantumReasoningJob]
    capabilities: dict[str, object]
    next_cursor: str | None


# Customer-selectable Tier-1 domains, mirror of bee/domains.py. Higher-tier
# Stage-0 families remain outside the public SDK type until promotion.
Domain = Literal[
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
    "accounting",
    "biology",
    "chemistry",
    "education",
    "mathematics",
    "physics",
]

# Customer-selectable production model ids accepted by the public API.
CustomerModelId = Literal[
    "bee-cell",
    "bee-brood",
    "bee-comb",
    "bee-buzz",
    "bee-hive",
    "bee-swarm",
]

# Internal trainable/deployment family names, mirror of bee/tiers.py. This is
# not the public request model field; use CustomerModelId for API calls.
ModelTier = Literal["cell", "brood", "comb", "buzz", "hive", "swarm", "enclave", "ignite"]


@dataclass
class ChatMessage:
    role: Literal["system", "user", "assistant"]
    content: str


class DomainIntelligenceMetadata(TypedDict):
    version: str
    primary_domain: str
    perspectives: list[str]
    serving: Literal["general", "baseline_specialist_synthesis", "specialist_adapter"]
    evidence_policy: Literal[
        "model_knowledge",
        "tenant_context_recommended",
        "live_sources_recommended",
        "live_sources_required",
    ]
    recommended_model: str | None
    notice: str | None


@dataclass
class ChatResponse:
    """Response shape from POST /chat/completions.

    Mirrors the OpenAI ChatCompletion shape because that's what the
    Bee API emits - preserves drop-in compatibility for callers that
    already know the OpenAI SDK.
    """

    id: str
    model: str
    content: str
    role: str = "assistant"
    finish_reason: str | None = None
    usage: dict = field(default_factory=dict)
    interaction_id: str | None = None
    domain_intelligence: DomainIntelligenceMetadata | None = None
    raw: dict = field(default_factory=dict)
