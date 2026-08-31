from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime, timedelta

from .audit import create_audit_event
from .contracts import MetricRollup, OutcomeObservation, SafetyReport, TraceContext
from .enums import ReviewSeverity
from .hashing import owner_hash
from .reviews import ALLOWED_SAFETY_CATEGORIES, create_review
from .rollups import ALLOWED_DIMENSIONS, compute_core_rollups

ALLOWED_OUTCOMES = frozenset({"RESOLVED", "PARTIALLY_RESOLVED", "NOT_RESOLVED", "ESCALATED_TO_VET", "UNKNOWN"})


class LabOperationsService:
    def __init__(self, repository, *, hash_secret: str, retention_days: int = 90, minimum_sample: int = 30, telemetry=None):
        self.repository = repository
        self.hash_secret = hash_secret
        self.retention_days = retention_days
        self.minimum_sample = minimum_sample
        self.telemetry = telemetry

    def audit(self, actor: str, action: str, target_type: str, target_id: str | None, correlation_id: str, *, outcome="SUCCEEDED", metadata=None):
        item = create_audit_event(self.hash_secret, actor, action, target_type, target_id, correlation_id, outcome=outcome, metadata=metadata)
        if not self.repository.append_audit(item): raise RuntimeError("LAB_AUDIT_WRITE_FAILED")
        return item

    def safety_report(self, owner: str, response, *, category: str, severity: ReviewSeverity, description: str | None = None):
        if category not in ALLOWED_SAFETY_CATEGORIES: raise ValueError("LAB_SAFETY_CATEGORY_INVALID")
        report_id = f"safety-{owner_hash(owner + ':' + response.id, self.hash_secret)[:32]}"
        item = SafetyReport(report_id, owner, owner_hash(owner, self.hash_secret), response.id,
            response.run_id or response.source_id, response.interaction_id, category, severity,
            description_ref=report_id if description else None,
            expires_at=datetime.now(UTC) + timedelta(days=self.retention_days))
        self.repository.put_safety_report(item)
        if description: self.repository.put_comment(report_id, description.strip()[:1000])
        review = create_review(item)
        self.repository.put_review(review)
        if self.telemetry:
            self.telemetry.emit("safety_report_submitted", context=TraceContext(
                correlation_id=response.interaction_id, interaction_id=response.interaction_id,
                deployment_id=response.deployment_id, environment=response.environment,
                data_classification=response.data_classification, run_id=response.run_id,
                owner_user_id=owner), properties={"source_type": response.source_type.value}, actor_type="USER")
        return item

    def outcome(self, owner: str, response, outcome_value: str):
        if outcome_value not in ALLOWED_OUTCOMES: raise ValueError("LAB_OUTCOME_INVALID")
        item = OutcomeObservation(f"outcome-{owner_hash(owner + ':' + response.id, self.hash_secret)[:32]}",
            owner, owner_hash(owner, self.hash_secret), response.run_id or response.source_id,
            response.id, outcome_value)
        self.repository.put_outcome(item); return item

    def recompute_rollups(self, now: datetime | None = None) -> list[MetricRollup]:
        result = compute_core_rollups(self.repository, minimum_sample=self.minimum_sample, now=now)
        for item in result:
            if set(item.dimensions) - ALLOWED_DIMENSIONS: raise ValueError("LAB_ROLLUP_DIMENSION_INVALID")
            self.repository.put_rollup(item)
        return result

    def expire(self, now: datetime | None = None) -> dict[str, int]:
        now = now or datetime.now(UTC); expired = {"events": 0, "comments": 0}
        events = getattr(self.repository, "events", None)
        if isinstance(events, dict):
            for key in [k for k, v in events.items() if v.expires_at and v.expires_at <= now]:
                events.pop(key); expired["events"] += 1
        feedback = self.repository.list_feedback()
        for item in feedback:
            if item.updated_at + timedelta(days=self.retention_days) <= now and item.id in getattr(self.repository, "comments", {}):
                self.repository.delete_comment(item.id); expired["comments"] += 1
        for item in self.repository.list_safety_reports():
            if item.expires_at and item.expires_at <= now and item.id in getattr(self.repository, "comments", {}):
                self.repository.delete_comment(item.id); expired["comments"] += 1
        return expired

    def audit_public(self, item):
        return asdict(item)
