from __future__ import annotations

from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from enum import Enum
from threading import RLock
from typing import Any

from .contracts import (
    AdminAuditEvent,
    AgentRunTrace,
    AgentStepTrace,
    EvaluationResult,
    EvidenceUsageTrace,
    HumanReview,
    InteractionResponse,
    MetricRollup,
    ModelCallTrace,
    OutcomeObservation,
    ResponseFeedback,
    SafetyDecisionTrace,
    SafetyReport,
    TelemetryEvent,
    ToolCallTrace,
)
from .enums import (
    DataClassification,
    FeedbackReason,
    FeedbackValue,
    ResponseSourceType,
    ReviewSeverity,
    ReviewStatus,
    RollupGranularity,
    TraceStatus,
)


def _serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


def _data(item: Any) -> dict[str, Any]:
    return _serialize(asdict(item))


def _rows(query: Any) -> list[dict[str, Any]]:
    result = []
    for snapshot in query.stream():
        row = dict(snapshot.to_dict() or {})
        row.setdefault("id", snapshot.id)
        result.append(row)
    return result


def _where(query: Any, field: str, value: Any) -> Any:
    return _filter(query, field, "==", value)


def _filter(query: Any, field: str, operator: str, value: Any) -> Any:
    try:
        from google.cloud.firestore_v1.base_query import FieldFilter  # type: ignore[import-untyped]
        return query.where(filter=FieldFilter(field, operator, value))
    except (ImportError, TypeError):
        return query.where(field, operator, value)


def _response(row: dict[str, Any]) -> InteractionResponse:
    data = dict(row)
    data["source_type"] = ResponseSourceType(data["source_type"])
    data["data_classification"] = DataClassification(data["data_classification"])
    return InteractionResponse(**{key: data[key] for key in InteractionResponse.__dataclass_fields__ if key in data})


def _feedback(row: dict[str, Any]) -> ResponseFeedback:
    data = dict(row)
    data["value"] = FeedbackValue(data["value"])
    data["reasons"] = [FeedbackReason(reason) for reason in data.get("reasons", [])]
    data["data_classification"] = DataClassification(data["data_classification"])
    return ResponseFeedback(**{key: data[key] for key in ResponseFeedback.__dataclass_fields__ if key in data})


def _run(row: dict[str, Any]) -> AgentRunTrace:
    data = dict(row)
    data["status"] = TraceStatus(data["status"])
    data["data_classification"] = DataClassification(data["data_classification"])
    return AgentRunTrace(**{key: data[key] for key in AgentRunTrace.__dataclass_fields__ if key in data})


def _step(row: dict[str, Any]) -> AgentStepTrace:
    data = dict(row)
    data["status"] = TraceStatus(data["status"])
    if "data_classification" in data:
        data["data_classification"] = DataClassification(data["data_classification"])
    return AgentStepTrace(**{key: data[key] for key in AgentStepTrace.__dataclass_fields__ if key in data})


def _model_call(row: dict[str, Any]) -> ModelCallTrace:
    data = dict(row)
    data["status"] = TraceStatus(data["status"])
    if "data_classification" in data:
        data["data_classification"] = DataClassification(data["data_classification"])
    return ModelCallTrace(**{key: data[key] for key in ModelCallTrace.__dataclass_fields__ if key in data})


def _typed(cls, row, **enums):
    data = dict(row)
    for key, enum in enums.items():
        if key in data: data[key] = enum(data[key])
    return cls(**{key: data[key] for key in cls.__dataclass_fields__ if key in data})


class FirestoreLabRepository:
    """Server-only Firestore adapter. Browser rules must deny these collections."""

    def __init__(self, client: Any, environment: str | None = None, *, comment_retention_days: int = 90) -> None:
        self.client = client
        self.environment = environment
        self.comment_retention_days = comment_retention_days
        self._lock = RLock()

    def append(self, event: TelemetryEvent) -> bool:
        ref = self.client.collection("telemetry_events").document(event.id)
        with self._lock:
            if ref.get().exists: return False
            try: ref.create(_data(event))
            except AttributeError: ref.set(_data(event))
            return True

    def list_events(self) -> list[TelemetryEvent]:
        rows = _rows(self.client.collection("telemetry_events"))
        items = []
        for row in rows:
            row["data_classification"] = DataClassification(row["data_classification"])
            items.append(TelemetryEvent(**{key: row[key] for key in TelemetryEvent.__dataclass_fields__ if key in row}))
        return sorted(items, key=lambda item: (item.occurred_at, item.id))

    def create(self, response: InteractionResponse) -> None:
        ref = self.client.collection("interaction_responses").document(response.id)
        with self._lock:
            if ref.get().exists: raise ValueError("LAB_RESPONSE_ALREADY_EXISTS")
            try: ref.create(_data(response))
            except AttributeError: ref.set(_data(response))

    def get_response(self, response_id: str) -> InteractionResponse | None:
        snapshot = self.client.collection("interaction_responses").document(response_id).get()
        return _response(dict(snapshot.to_dict() or {})) if snapshot.exists else None

    def list_responses(self) -> list[InteractionResponse]:
        return sorted((_response(row) for row in _rows(self.client.collection("interaction_responses"))), key=lambda item: (item.published_at, item.id))

    def get_feedback(self, feedback_id: str) -> ResponseFeedback | None:
        snapshot = self.client.collection("response_feedback").document(feedback_id).get()
        return _feedback(dict(snapshot.to_dict() or {})) if snapshot.exists else None

    def put(self, feedback: ResponseFeedback) -> ResponseFeedback:
        ref = self.client.collection("response_feedback").document(feedback.id)
        if hasattr(self.client, "transaction"):
            from google.cloud.firestore_v1.transaction import (
                transactional,  # type: ignore[import-untyped]
            )
            transaction = self.client.transaction()
            @transactional
            def upsert(tx):
                snapshot = tx.get(ref)
                item = feedback
                if snapshot.exists:
                    current = _feedback(dict(snapshot.to_dict() or {}))
                    item = replace(feedback, revision=current.revision + 1, created_at=current.created_at)
                tx.set(ref, _data(item)); return item
            return upsert(transaction)
        with self._lock:
            snapshot = ref.get(); item = feedback
            if snapshot.exists:
                current = _feedback(dict(snapshot.to_dict() or {}))
                item = replace(feedback, revision=current.revision + 1, created_at=current.created_at)
            ref.set(_data(item)); return item

    def list_feedback(self) -> list[ResponseFeedback]:
        return sorted((_feedback(row) for row in _rows(self.client.collection("response_feedback"))), key=lambda item: (item.updated_at, item.id))

    def put_comment(
        self, feedback_id: str, comment: str, *, owner_user_id: str | None = None
    ) -> None:
        now = datetime.now(UTC)
        self.client.collection("feedback_comments").document(feedback_id).set(
            {"feedback_id": feedback_id, "comment": comment,
             "owner_user_id": owner_user_id, "redaction_status": "VALIDATED",
             "data_classification": "USER_CONTENT", "updated_at": now,
             "expires_at": now + timedelta(days=self.comment_retention_days)}
        )

    def get_comment(self, feedback_id: str) -> str | None:
        snapshot = self.client.collection("feedback_comments").document(feedback_id).get()
        if not snapshot.exists:
            return None
        value = (snapshot.to_dict() or {}).get("comment")
        return value if isinstance(value, str) else None

    def delete_comment(self, feedback_id: str) -> None:
        self.client.collection("feedback_comments").document(feedback_id).delete()

    def put_with_comment(self, feedback: ResponseFeedback, comment: str | None) -> ResponseFeedback:
        if not hasattr(self.client, "transaction"):
            stored = self.put(feedback)
            self.put_comment(
                feedback.id, comment, owner_user_id=feedback.owner_user_id
            ) if comment is not None else self.delete_comment(feedback.id)
            return stored
        from google.cloud.firestore_v1.transaction import (
            transactional,  # type: ignore[import-untyped]
        )
        feedback_ref = self.client.collection("response_feedback").document(feedback.id)
        comment_ref = self.client.collection("feedback_comments").document(feedback.id)
        transaction = self.client.transaction()
        @transactional
        def upsert(tx):
            snapshot = tx.get(feedback_ref); item = feedback
            if snapshot.exists:
                current = _feedback(dict(snapshot.to_dict() or {}))
                item = replace(feedback, revision=current.revision + 1, created_at=current.created_at)
            tx.set(feedback_ref, _data(item))
            if comment is None: tx.delete(comment_ref)
            else:
                now = datetime.now(UTC)
                tx.set(comment_ref, {"feedback_id": feedback.id, "comment": comment,
                    "owner_user_id": feedback.owner_user_id,
                    "redaction_status": "VALIDATED", "data_classification": "USER_CONTENT",
                    "updated_at": now, "expires_at": now + timedelta(days=self.comment_retention_days)})
            return item
        return upsert(transaction)

    def put_run(self, trace: AgentRunTrace) -> None:
        self.client.collection("agent_run_traces").document(trace.run_id).set(_data(trace))

    def _transition(self, collection: str, entity_id: str, item: Any, hydrate, allowed_from: set[TraceStatus], error: str) -> None:
        ref = self.client.collection(collection).document(entity_id)
        if hasattr(self.client, "transaction"):
            from google.cloud.firestore_v1.transaction import (
                transactional,  # type: ignore[import-untyped]
            )
            transaction = self.client.transaction()

            @transactional
            def update(tx):
                snapshot = tx.get(ref)
                if not snapshot.exists:
                    raise ValueError(f"{error}_NOT_FOUND")
                current = hydrate(dict(snapshot.to_dict() or {}))
                if current.status is item.status and current.status is not TraceStatus.STARTED:
                    return
                if current.status not in allowed_from:
                    raise ValueError(f"{error}_TRANSITION_INVALID")
                tx.set(ref, _data(item))

            update(transaction)
            return
        with self._lock:
            snapshot = ref.get()
            if not snapshot.exists:
                raise ValueError(f"{error}_NOT_FOUND")
            current = hydrate(dict(snapshot.to_dict() or {}))
            if current.status is item.status and current.status is not TraceStatus.STARTED:
                return
            if current.status not in allowed_from:
                raise ValueError(f"{error}_TRANSITION_INVALID")
            ref.set(_data(item))

    def transition_run(self, trace: AgentRunTrace, allowed_from: set[TraceStatus]) -> None:
        self._transition("agent_run_traces", trace.run_id, trace, _run, allowed_from, "LAB_RUN_TRACE")

    def get_run(self, run_id: str) -> AgentRunTrace | None:
        snapshot = self.client.collection("agent_run_traces").document(run_id).get()
        return _run(dict(snapshot.to_dict() or {})) if snapshot.exists else None

    def list_runs(self) -> list[AgentRunTrace]:
        return sorted((_run(row) for row in _rows(self.client.collection("agent_run_traces"))), key=lambda item: (item.started_at, item.run_id))

    def page_runs(self, *, limit: int, cursor: str | None = None, status: str | None = None,
        agent_id: str | None = None, safety_state: str | None = None,
        started_after=None, started_before=None) -> tuple[list[AgentRunTrace], str | None]:
        query = self.client.collection("agent_run_traces")
        if self.environment: query = _where(query, "environment", self.environment)
        if status: query = _where(query, "status", status)
        if agent_id: query = _where(query, "agent_type", agent_id)
        if safety_state: query = _where(query, "safety_state", safety_state)
        if started_after: query = _filter(query, "started_at", ">=", started_after)
        if started_before: query = _filter(query, "started_at", "<=", started_before)
        query = query.order_by("started_at", direction="DESCENDING").order_by("run_id")
        if cursor:
            snapshot = self.client.collection("agent_run_traces").document(cursor).get()
            if not snapshot.exists: raise ValueError("LAB_CURSOR_INVALID")
            query = query.start_after(snapshot)
        rows = _rows(query.limit(limit + 1)); items = [_run(row) for row in rows[:limit]]
        return items, items[-1].run_id if len(rows) > limit and items else None

    def put_step(self, trace: AgentStepTrace) -> None:
        self.client.collection("agent_step_traces").document(trace.id).set(_data(trace))

    def transition_step(self, trace: AgentStepTrace, allowed_from: set[TraceStatus]) -> None:
        self._transition("agent_step_traces", trace.id, trace, _step, allowed_from, "LAB_STEP_TRACE")

    def list_steps(self, run_id: str | None = None) -> list[AgentStepTrace]:
        query = self.client.collection("agent_step_traces")
        if run_id is not None:
            query = _where(query, "run_id", run_id)
        return sorted((_step(row) for row in _rows(query)), key=lambda item: (item.started_at, item.id))

    def put_model_call(self, trace: ModelCallTrace) -> None:
        self.client.collection("model_call_traces").document(trace.id).set(_data(trace))

    def transition_model_call(self, trace: ModelCallTrace, allowed_from: set[TraceStatus]) -> None:
        self._transition("model_call_traces", trace.id, trace, _model_call, allowed_from, "LAB_MODEL_TRACE")

    def list_model_calls(self, run_id: str | None = None) -> list[ModelCallTrace]:
        query = self.client.collection("model_call_traces")
        if run_id is not None:
            query = _where(query, "run_id", run_id)
        return sorted((_model_call(row) for row in _rows(query)), key=lambda item: (item.started_at, item.id))

    def put_tool_call(self, trace: ToolCallTrace) -> None:
        self.client.collection("tool_call_traces").document(trace.id).set(_data(trace))

    def transition_tool_call(self, trace: ToolCallTrace, allowed_from: set[TraceStatus]) -> None:
        self._transition("tool_call_traces", trace.id, trace,
            lambda row: _typed(ToolCallTrace, row, status=TraceStatus,
                data_classification=DataClassification), allowed_from, "LAB_TOOL_TRACE")

    def put_safety_decision(self, trace: SafetyDecisionTrace) -> None:
        self.client.collection("safety_decision_traces").document(trace.id).set(_data(trace))

    def put_evidence_usage(self, trace: EvidenceUsageTrace) -> None:
        self.client.collection("evidence_usage_traces").document(trace.id).set(_data(trace))

    def list_tool_calls(self, run_id: str | None = None) -> list[ToolCallTrace]:
        query = self.client.collection("tool_call_traces")
        query = _where(query, "run_id", run_id) if run_id else query
        return sorted((_typed(ToolCallTrace, row, status=TraceStatus, data_classification=DataClassification) for row in _rows(query)), key=lambda x: (x.started_at, x.id))

    def list_safety_decisions(self, run_id: str | None = None) -> list[SafetyDecisionTrace]:
        query = self.client.collection("safety_decision_traces")
        query = _where(query, "run_id", run_id) if run_id else query
        return sorted((_typed(SafetyDecisionTrace, row, data_classification=DataClassification) for row in _rows(query)), key=lambda x: (x.decided_at, x.id))

    def list_evidence_usage(self, run_id: str | None = None) -> list[EvidenceUsageTrace]:
        query = self.client.collection("evidence_usage_traces")
        query = _where(query, "run_id", run_id) if run_id else query
        return sorted((_typed(EvidenceUsageTrace, row, data_classification=DataClassification) for row in _rows(query)), key=lambda x: (x.recorded_at, x.id))

    def put_safety_report(self, item: SafetyReport) -> None:
        ref = self.client.collection("safety_reports").document(item.id)
        if ref.get().exists: raise ValueError("LAB_SAFETY_REPORT_ALREADY_EXISTS")
        ref.set(_data(item))

    def list_safety_reports(self) -> list[SafetyReport]:
        return sorted((_typed(SafetyReport, row, severity=ReviewSeverity, status=ReviewStatus) for row in _rows(self.client.collection("safety_reports"))), key=lambda x: (x.created_at, x.id))

    def put_outcome(self, item: OutcomeObservation) -> None:
        self.client.collection("outcome_observations").document(item.id).set(_data(item))

    def list_outcomes(self) -> list[OutcomeObservation]:
        return sorted((_typed(OutcomeObservation, row) for row in _rows(self.client.collection("outcome_observations"))), key=lambda x: (x.observed_at, x.id))

    def put_review(self, item: HumanReview) -> None:
        self.client.collection("human_reviews").document(item.id).set(_data(item))

    def list_reviews(self) -> list[HumanReview]:
        return sorted((_typed(HumanReview, row, severity=ReviewSeverity, status=ReviewStatus) for row in _rows(self.client.collection("human_reviews"))), key=lambda x: (x.created_at, x.id))

    def put_rollup(self, item: MetricRollup) -> None:
        self.client.collection("metric_rollups").document(item.id).set(_data(item))

    def list_rollups(self) -> list[MetricRollup]:
        return sorted((_typed(MetricRollup, row, granularity=RollupGranularity) for row in _rows(self.client.collection("metric_rollups"))), key=lambda x: (x.bucket, x.id))

    def put_evaluation(self, item: EvaluationResult) -> None:
        ref = self.client.collection("evaluation_results").document(item.id)
        snapshot = ref.get()
        if snapshot.exists:
            current = _typed(EvaluationResult, dict(snapshot.to_dict() or {}))
            if current != item:
                raise ValueError("LAB_EVALUATION_IMMUTABLE")
            return
        try: ref.create(_data(item))
        except AttributeError: ref.set(_data(item))

    def list_evaluations(self) -> list[EvaluationResult]:
        return sorted((_typed(EvaluationResult, row) for row in _rows(
            self.client.collection("evaluation_results"))), key=lambda x: (x.evaluated_at, x.id))

    def append_audit(self, item: AdminAuditEvent) -> bool:
        ref = self.client.collection("admin_audit_events").document(item.id)
        try:
            ref.create(_data(item)); return True
        except AttributeError:
            if ref.get().exists: return False
            ref.set(_data(item)); return True

    def list_audit(self) -> list[AdminAuditEvent]:
        return sorted((_typed(AdminAuditEvent, row) for row in _rows(self.client.collection("admin_audit_events"))), key=lambda x: (x.occurred_at, x.id))

    def delete_owner_lab_data(self, owner: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        selected: dict[str, list[Any]] = {}
        for collection in ("interaction_responses", "response_feedback", "agent_run_traces", "safety_reports", "outcome_observations"):
            selected[collection] = list(_where(self.client.collection(collection), "owner_user_id", owner).stream())
        run_ids = {snapshot.id for snapshot in selected["agent_run_traces"]}
        feedback_ids = {snapshot.id for snapshot in selected["response_feedback"]}
        report_ids = {snapshot.id for snapshot in selected["safety_reports"]}
        for collection, rows in selected.items():
            for snapshot in rows: snapshot.reference.delete()
            counts[collection] = len(rows)
        for collection in ("agent_step_traces", "model_call_traces", "tool_call_traces", "safety_decision_traces", "evidence_usage_traces"):
            rows = [snap for run_id in run_ids for snap in _where(self.client.collection(collection), "run_id", run_id).stream()]
            for snapshot in rows: snapshot.reference.delete()
            counts[collection] = len(rows)
        review_rows = [snap for report_id in report_ids for snap in _where(self.client.collection("human_reviews"), "safety_report_id", report_id).stream()]
        for snapshot in review_rows: snapshot.reference.delete()
        counts["human_reviews"] = len(review_rows)
        comment_ids = feedback_ids | report_ids
        for item_id in comment_ids: self.client.collection("feedback_comments").document(item_id).delete()
        counts["feedback_comments"] = len(comment_ids)
        return counts
