from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class AnalysisStatus(StrEnum):
    CREATED = "CREATED"
    FUNDING_RESERVED = "FUNDING_RESERVED"
    QUEUED = "QUEUED"
    PREPARING_MEDIA = "PREPARING_MEDIA"
    CALLING_PROVIDER = "CALLING_PROVIDER"
    VALIDATING_OUTPUT = "VALIDATING_OUTPUT"
    APPLYING_GUARDRAILS = "APPLYING_GUARDRAILS"
    APPLYING_SAFETY = "APPLYING_SAFETY"
    PERSISTING_RESULT = "PERSISTING_RESULT"
    COMPLETED = "COMPLETED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_FINAL = "FAILED_FINAL"
    CANCELED = "CANCELED"


LEGAL_TRANSITIONS = {
    AnalysisStatus.CREATED: {AnalysisStatus.FUNDING_RESERVED, AnalysisStatus.CANCELED},
    AnalysisStatus.FUNDING_RESERVED: {AnalysisStatus.QUEUED, AnalysisStatus.FAILED_FINAL},
    AnalysisStatus.QUEUED: {
        AnalysisStatus.PREPARING_MEDIA,
        AnalysisStatus.FAILED_RETRYABLE,
        AnalysisStatus.FAILED_FINAL,
        AnalysisStatus.CANCELED,
    },
    AnalysisStatus.PREPARING_MEDIA: {
        AnalysisStatus.CALLING_PROVIDER,
        AnalysisStatus.FAILED_RETRYABLE,
        AnalysisStatus.FAILED_FINAL,
    },
    AnalysisStatus.CALLING_PROVIDER: {
        AnalysisStatus.VALIDATING_OUTPUT,
        AnalysisStatus.FAILED_RETRYABLE,
        AnalysisStatus.FAILED_FINAL,
    },
    AnalysisStatus.VALIDATING_OUTPUT: {
        AnalysisStatus.APPLYING_GUARDRAILS,
        AnalysisStatus.FAILED_FINAL,
    },
    AnalysisStatus.APPLYING_GUARDRAILS: {
        AnalysisStatus.APPLYING_SAFETY,
        AnalysisStatus.FAILED_FINAL,
    },
    AnalysisStatus.APPLYING_SAFETY: {AnalysisStatus.PERSISTING_RESULT, AnalysisStatus.FAILED_FINAL},
    AnalysisStatus.PERSISTING_RESULT: {AnalysisStatus.COMPLETED, AnalysisStatus.FAILED_FINAL},
    AnalysisStatus.FAILED_RETRYABLE: {
        AnalysisStatus.QUEUED,
        AnalysisStatus.PREPARING_MEDIA,
        AnalysisStatus.FAILED_FINAL,
    },
}


def transition(current: AnalysisStatus, target: AnalysisStatus) -> AnalysisStatus:
    if target not in LEGAL_TRANSITIONS.get(current, set()):
        raise ValueError(f"ILLEGAL_ANALYSIS_TRANSITION:{current}->{target}")
    return target


@dataclass
class AnalysisJob:
    id: str
    owner_user_id: str
    animal_id: str
    species: str
    analysis_type: str
    media_asset_ids: list[str]
    idempotency_key: str
    operation_request_id: str
    funding_reservation_id: str
    species_pack_version: str = "DOG-v1"
    prompt_id: str = "platform_smoke"
    prompt_version: str = "1.0.0"
    schema_id: str = "platform_smoke"
    schema_version: str = "1.0.0"
    guardrail_version: str = "1.0.0"
    safety_policy_version: str = "1.0.0"
    media_preparation_version: str = "1.0.0"
    provider: str = "FAKE"
    provider_model: str = "fake-platform-smoke-v1"
    provider_config_version: str = "local-v1"
    status: AnalysisStatus = AnalysisStatus.FUNDING_RESERVED
    attempt_count: int = 0
    provider_call_count: int = 0
    correlation_id: str | None = None
    response_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    queued_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    last_error_code: str | None = None
    prompt_hash: str | None = None
    schema_hash: str | None = None
    user_context: str | None = None


@dataclass
class AnalysisResult:
    id: str
    job_id: str
    owner_user_id: str
    animal_id: str
    analysis_type: str
    schema_id: str
    schema_version: str
    structured_payload: dict
    validation_status: str
    semantic_guardrail_status: str
    safety_state: str
    safety_reasons: list[str]
    provider: str
    provider_model: str
    prompt_version: str
    guardrail_version: str
    safety_policy_version: str
    media_preparation_version: str
    species_pack_version: str
    provider_usage_metadata: dict
    cost_metadata: dict
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    prompt_hash: str | None = None
    schema_hash: str | None = None
    media_asset_ids: list[str] = field(default_factory=list)
    provider_config_version: str = "local-v1"
