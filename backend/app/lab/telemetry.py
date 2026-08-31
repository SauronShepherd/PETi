from __future__ import annotations

import json
import logging
from datetime import timedelta
from typing import Any
from uuid import uuid4

from .contracts import TelemetryEvent, TraceContext, utcnow
from .hashing import owner_hash
from .redaction import validate_event_properties
from .repositories import TelemetryEventRepository

logger = logging.getLogger(__name__)

ALLOWED_EVENT_PROPERTIES: dict[str, frozenset[str]] = {
    "api_request_completed": frozenset({"route_template", "method", "status_code", "duration_ms", "role_class"}),
    "run_created": frozenset({"agent_type", "goal_type"}),
    "run_queued": frozenset({"agent_type"}),
    "run_started": frozenset({"agent_type"}),
    "run_completed": frozenset({"agent_type", "outcome", "safety_state", "duration_ms"}),
    "run_failed": frozenset({"agent_type", "error_code", "retryable", "duration_ms"}),
    "run_cancelled": frozenset({"agent_type"}),
    "agent_step_started": frozenset({"agent_id", "agent_version", "schema_version"}),
    "agent_step_completed": frozenset(
        {"agent_id", "agent_version", "outcome", "safety_state", "duration_ms", "evidence_count", "claim_count"}
    ),
    "agent_step_failed": frozenset({"agent_id", "error_code", "retryable"}),
    "agent_handoff": frozenset({"from_agent", "to_agent", "reason_code", "evidence_count"}),
    "model_call_started": frozenset({"provider", "model_id", "prompt_version", "schema_version"}),
    "model_call_completed": frozenset(
        {"provider", "model_id", "latency_ms", "input_tokens", "output_tokens", "cached_input_tokens", "usage_status"}
    ),
    "model_call_failed": frozenset({"provider", "model_id", "latency_ms", "error_code", "retryable"}),
    "response_published": frozenset({"source_type", "outcome", "safety_state", "feedback_eligible"}),
    "feedback_submitted": frozenset({"value", "reasons", "has_comment"}),
    "feedback_updated": frozenset({"value", "reasons", "has_comment", "revision"}),
    "feedback_removed": frozenset({"revision"}),
    "safety_report_submitted": frozenset({"source_type"}),
}

class TelemetryService:
    def __init__(
        self,
        repository: TelemetryEventRepository,
        *,
        hash_secret: str,
        retention_days: int = 90,
        enabled: bool = True,
    ) -> None:
        self.repository = repository
        self.hash_secret = hash_secret
        self.retention_days = retention_days
        self.enabled = enabled
        self.invalid_event_count = 0
        self.write_failure_count = 0
        self.attempted_event_count = 0
        self.written_event_count = 0
        self.dropped_event_count = 0

    def emit(
        self,
        event_name: str,
        *,
        context: TraceContext,
        properties: dict[str, Any] | None = None,
        event_id: str | None = None,
        actor_type: str = "SYSTEM",
    ) -> TelemetryEvent | None:
        if not self.enabled:
            self.dropped_event_count += 1
            return None
        self.attempted_event_count += 1
        clean = self._validate(event_name, properties or {})
        now = utcnow()
        event = TelemetryEvent(
            id=event_id or str(uuid4()),
            event_name=event_name,
            environment=context.environment,
            data_classification=context.data_classification,
            correlation_id=context.correlation_id,
            interaction_id=context.interaction_id,
            run_id=context.run_id,
            step_id=context.step_id,
            actor_type=actor_type,
            actor_id_hash=(owner_hash(context.owner_user_id, self.hash_secret) if context.owner_user_id else None),
            deployment_id=context.deployment_id,
            properties=clean,
            occurred_at=now,
            received_at=now,
            expires_at=now + timedelta(days=self.retention_days),
        )
        try:
            if self.repository.append(event):
                self.written_event_count += 1
            return event
        except Exception:  # noqa: BLE001 - telemetry is explicitly fail-open
            self.write_failure_count += 1
            self.dropped_event_count += 1
            logger.warning("lab_telemetry_write_failed", extra={"event_name": event_name})
            return None

    def _validate(self, event_name: str, properties: dict[str, Any]) -> dict[str, Any]:
        allowed = ALLOWED_EVENT_PROPERTIES.get(event_name)
        if allowed is None:
            self.invalid_event_count += 1
            raise ValueError("LAB_EVENT_NOT_ALLOWED")
        try:
            clean = validate_event_properties(properties, allowed)
            if len(json.dumps(clean, ensure_ascii=False).encode()) > 32_768:
                raise ValueError("LAB_EVENT_TOO_LARGE")
            return clean
        except ValueError:
            self.invalid_event_count += 1
            raise
