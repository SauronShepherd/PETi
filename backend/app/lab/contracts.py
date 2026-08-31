from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from .enums import (
    DataClassification,
    FeedbackReason,
    FeedbackValue,
    ResponseSourceType,
    ReviewSeverity,
    ReviewStatus,
    RollupGranularity,
    RufsState,
    TraceStatus,
)


def utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class TraceContext:
    correlation_id: str
    interaction_id: str
    deployment_id: str
    environment: str
    data_classification: DataClassification
    run_id: str | None = None
    step_id: str | None = None
    owner_user_id: str | None = None
    pet_id: str | None = None
    agent_id: str | None = None
    experiment_id: str | None = None
    variant_id: str | None = None


@dataclass
class TelemetryEvent:
    event_name: str
    environment: str
    data_classification: DataClassification
    correlation_id: str
    properties: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    schema_version: str = "1.0.0"
    occurred_at: datetime = field(default_factory=utcnow)
    received_at: datetime = field(default_factory=utcnow)
    interaction_id: str | None = None
    run_id: str | None = None
    step_id: str | None = None
    actor_type: str = "SYSTEM"
    actor_id_hash: str | None = None
    deployment_id: str = "local"
    expires_at: datetime | None = None

    def public(self) -> dict[str, Any]:
        data = asdict(self)
        data["data_classification"] = self.data_classification.value
        return data


@dataclass
class InteractionResponse:
    owner_user_id: str
    owner_hash: str
    interaction_id: str
    source_type: ResponseSourceType
    source_id: str
    outcome: str
    safety_state: str
    deployment_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    run_id: str | None = None
    response_version: int = 1
    supersedes_response_id: str | None = None
    content_ref: str | None = None
    agent_version_set: dict[str, str] = field(default_factory=dict)
    model_version_set: list[dict[str, str]] = field(default_factory=list)
    eligible_for_feedback: bool = True
    environment: str = "LOCAL"
    data_classification: DataClassification = DataClassification.TEST
    published_at: datetime = field(default_factory=utcnow)
    deleted_at: datetime | None = None

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "interaction_id": self.interaction_id,
            "run_id": self.run_id,
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "response_version": self.response_version,
            "supersedes_response_id": self.supersedes_response_id,
            "outcome": self.outcome,
            "safety_state": self.safety_state,
            "eligible_for_feedback": self.eligible_for_feedback,
            "published_at": self.published_at,
        }


@dataclass
class ResponseFeedback:
    id: str
    owner_user_id: str
    owner_hash: str
    response_id: str
    interaction_id: str
    value: FeedbackValue
    reasons: list[FeedbackReason]
    run_id: str | None = None
    comment_ref: str | None = None
    safety_report: bool = False
    source: str = "WEB"
    locale: str | None = None
    client_version: str | None = None
    revision: int = 1
    environment: str = "LOCAL"
    data_classification: DataClassification = DataClassification.TEST
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    removed_at: datetime | None = None

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "response_id": self.response_id,
            "run_id": self.run_id,
            "value": self.value.value,
            "reasons": [reason.value for reason in self.reasons],
            "safety_report": self.safety_report,
            "revision": self.revision,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "removed_at": self.removed_at,
        }


@dataclass
class AgentRunTrace:
    run_id: str
    interaction_id: str
    correlation_id: str
    owner_user_id: str
    owner_hash: str
    pet_id: str | None
    agent_type: str
    deployment_id: str
    environment: str
    data_classification: DataClassification
    status: TraceStatus = TraceStatus.STARTED
    plan_id: str | None = None
    recipe_id: str | None = None
    outcome: str | None = None
    safety_state: str | None = None
    response_id: str | None = None
    started_at: datetime = field(default_factory=utcnow)
    completed_at: datetime | None = None
    duration_ms: int | None = None
    expires_at: datetime | None = None


@dataclass
class AgentStepTrace:
    id: str
    run_id: str
    step_id: str
    agent_id: str
    agent_version: str
    schema_version: str
    status: TraceStatus
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = None
    evidence_count: int = 0
    claim_count: int = 0
    safety_state: str | None = None
    outcome: str | None = None
    correlation_id: str = "unknown"
    deployment_id: str = "unknown"
    environment: str = "LOCAL"
    data_classification: DataClassification = DataClassification.TEST
    dependency_ids: tuple[str, ...] = ()
    budget_snapshot: dict[str, int] = field(default_factory=dict)
    expires_at: datetime | None = None
    owner_user_id: str | None = None
    owner_hash: str | None = None


@dataclass
class ModelCallTrace:
    id: str
    run_id: str | None
    step_id: str | None
    agent_id: str | None
    correlation_id: str
    provider: str
    model_id: str
    status: TraceStatus
    started_at: datetime
    prompt_version: str = "unknown"
    schema_version: str = "unknown"
    safety_policy_version: str = "unknown"
    completed_at: datetime | None = None
    latency_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_input_tokens: int | None = None
    provider_request_id: str | None = None
    attempt_count: int = 1
    error_code: str | None = None
    retryable: bool | None = None
    usage_status: str = "UNKNOWN"
    deployment_id: str = "local"
    environment: str = "LOCAL"
    data_classification: DataClassification = DataClassification.TEST
    expires_at: datetime | None = None
    owner_user_id: str | None = None
    owner_hash: str | None = None


@dataclass
class ToolCallTrace:
    id: str
    run_id: str
    step_id: str
    agent_id: str
    tool_id: str
    status: TraceStatus
    correlation_id: str
    deployment_id: str
    environment: str
    data_classification: DataClassification
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = None
    result_code: str | None = None
    expires_at: datetime | None = None
    owner_user_id: str | None = None
    owner_hash: str | None = None


@dataclass
class SafetyDecisionTrace:
    id: str
    run_id: str
    step_id: str
    decision: str
    policy_version: str
    correlation_id: str
    deployment_id: str
    environment: str
    data_classification: DataClassification
    decided_at: datetime = field(default_factory=utcnow)
    expires_at: datetime | None = None
    owner_user_id: str | None = None
    owner_hash: str | None = None


@dataclass
class EvidenceUsageTrace:
    id: str
    run_id: str
    step_id: str
    modality: str
    selected_count: int
    claim_count: int
    correlation_id: str
    deployment_id: str
    environment: str
    data_classification: DataClassification
    recorded_at: datetime = field(default_factory=utcnow)
    expires_at: datetime | None = None
    owner_user_id: str | None = None
    owner_hash: str | None = None


@dataclass(frozen=True)
class RufsClassification:
    useful: RufsState
    grounded: RufsState
    safe: RufsState
    overall: RufsState
    reasons: tuple[str, ...] = ()


@dataclass
class SafetyReport:
    id: str
    owner_user_id: str
    owner_hash: str
    response_id: str
    run_id: str
    interaction_id: str
    category: str
    severity: ReviewSeverity
    description_ref: str | None = None
    status: ReviewStatus = ReviewStatus.OPEN
    created_at: datetime = field(default_factory=utcnow)
    expires_at: datetime | None = None

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id, "response_id": self.response_id, "run_id": self.run_id,
            "category": self.category, "severity": self.severity.value,
            "status": self.status.value, "created_at": self.created_at,
        }


@dataclass
class OutcomeObservation:
    id: str
    owner_user_id: str
    owner_hash: str
    run_id: str
    response_id: str | None
    outcome_value: str
    source: str = "USER"
    observed_at: datetime = field(default_factory=utcnow)
    removed_at: datetime | None = None

    def public(self) -> dict[str, Any]:
        return {"id": self.id, "run_id": self.run_id, "response_id": self.response_id,
            "outcome_value": self.outcome_value, "source": self.source,
            "observed_at": self.observed_at, "removed_at": self.removed_at}


@dataclass
class HumanReview:
    id: str
    safety_report_id: str
    run_id: str
    response_id: str
    severity: ReviewSeverity
    status: ReviewStatus = ReviewStatus.OPEN
    assigned_reviewer_hash: str | None = None
    resolution: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class MetricRollup:
    id: str
    bucket: str
    granularity: RollupGranularity
    metric_name: str
    dimensions: dict[str, str]
    numerator: int
    denominator: int
    sample_count: int
    value: float | None
    preliminary: bool
    computed_at: datetime = field(default_factory=utcnow)
    schema_version: str = "1.0.0"


@dataclass
class EvaluationResult:
    id: str
    suite: str
    deployment_id: str
    release_id: str
    status: str
    critical_gates: dict[str, str]
    metrics: dict[str, float | None]
    source_manifest_id: str
    evaluated_at: datetime = field(default_factory=utcnow)
    schema_version: str = "1.0.0"


@dataclass
class AdminAuditEvent:
    id: str
    action: str
    actor_hash: str
    target_type: str
    target_id_hash: str | None
    outcome: str
    correlation_id: str
    occurred_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, str] = field(default_factory=dict)
