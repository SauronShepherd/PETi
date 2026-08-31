from __future__ import annotations

from dataclasses import replace
from threading import RLock
from typing import Protocol

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
from .enums import TraceStatus


class TelemetryEventRepository(Protocol):
    def append(self, event: TelemetryEvent) -> bool: ...
    def list_events(self) -> list[TelemetryEvent]: ...


class ResponseRepository(Protocol):
    def create(self, response: InteractionResponse) -> None: ...
    def get(self, response_id: str) -> InteractionResponse | None: ...


class FeedbackRepository(Protocol):
    def get(self, feedback_id: str) -> ResponseFeedback | None: ...
    def put(self, feedback: ResponseFeedback) -> ResponseFeedback: ...


class TraceRepository(Protocol):
    def put_run(self, trace: AgentRunTrace) -> None: ...
    def get_run(self, run_id: str) -> AgentRunTrace | None: ...
    def put_step(self, trace: AgentStepTrace) -> None: ...
    def put_model_call(self, trace: ModelCallTrace) -> None: ...


class InMemoryLabRepository:
    def __init__(self) -> None:
        self.events: dict[str, TelemetryEvent] = {}
        self.responses: dict[str, InteractionResponse] = {}
        self.feedback: dict[str, ResponseFeedback] = {}
        self.run_traces: dict[str, AgentRunTrace] = {}
        self.step_traces: dict[str, AgentStepTrace] = {}
        self.model_call_traces: dict[str, ModelCallTrace] = {}
        self.tool_call_traces: dict[str, ToolCallTrace] = {}
        self.safety_decision_traces: dict[str, SafetyDecisionTrace] = {}
        self.evidence_usage_traces: dict[str, EvidenceUsageTrace] = {}
        self.comments: dict[str, str] = {}
        self.safety_reports: dict[str, SafetyReport] = {}
        self.outcomes: dict[str, OutcomeObservation] = {}
        self.reviews: dict[str, HumanReview] = {}
        self.rollups: dict[str, MetricRollup] = {}
        self.evaluations: dict[str, EvaluationResult] = {}
        self.audit_events: dict[str, AdminAuditEvent] = {}
        self._lock = RLock()

    def append(self, event: TelemetryEvent) -> bool:
        with self._lock:
            if event.id in self.events:
                return False
            self.events[event.id] = event
            return True

    def list_events(self) -> list[TelemetryEvent]:
        return sorted(self.events.values(), key=lambda item: (item.occurred_at, item.id))

    def create(self, response: InteractionResponse) -> None:
        with self._lock:
            if response.id in self.responses:
                raise ValueError("LAB_RESPONSE_ALREADY_EXISTS")
            self.responses[response.id] = response

    def get(self, entity_id: str):
        if entity_id in self.responses:
            return self.responses[entity_id]
        return self.feedback.get(entity_id)

    def get_response(self, response_id: str) -> InteractionResponse | None:
        return self.responses.get(response_id)

    def list_responses(self) -> list[InteractionResponse]:
        return sorted(self.responses.values(), key=lambda item: (item.published_at, item.id))

    def get_feedback(self, feedback_id: str) -> ResponseFeedback | None:
        return self.feedback.get(feedback_id)

    def list_feedback(self) -> list[ResponseFeedback]:
        return sorted(self.feedback.values(), key=lambda item: (item.updated_at, item.id))

    def put(self, feedback: ResponseFeedback) -> ResponseFeedback:
        with self._lock:
            current = self.feedback.get(feedback.id)
            if current:
                feedback = replace(
                    feedback,
                    revision=current.revision + 1,
                    created_at=current.created_at,
                )
            self.feedback[feedback.id] = feedback
            return feedback

    def put_comment(self, feedback_id: str, comment: str) -> None:
        self.comments[feedback_id] = comment

    def get_comment(self, feedback_id: str) -> str | None:
        return self.comments.get(feedback_id)

    def delete_comment(self, feedback_id: str) -> None:
        self.comments.pop(feedback_id, None)

    def put_with_comment(self, feedback: ResponseFeedback, comment: str | None) -> ResponseFeedback:
        with self._lock:
            stored = self.put(feedback)
            if comment is None: self.comments.pop(feedback.id, None)
            else: self.comments[feedback.id] = comment
            return stored

    def put_run(self, trace: AgentRunTrace) -> None:
        self.run_traces[trace.run_id] = trace

    def transition_run(self, trace: AgentRunTrace, allowed_from: set[TraceStatus]) -> None:
        with self._lock:
            current = self.run_traces.get(trace.run_id)
            if current is None:
                raise ValueError("LAB_RUN_TRACE_NOT_FOUND")
            if current.status is trace.status and current.status is not TraceStatus.STARTED:
                return
            if current.status not in allowed_from:
                raise ValueError("LAB_RUN_TRACE_TRANSITION_INVALID")
            self.run_traces[trace.run_id] = trace

    def get_run(self, run_id: str) -> AgentRunTrace | None:
        return self.run_traces.get(run_id)

    def list_runs(self) -> list[AgentRunTrace]:
        return sorted(self.run_traces.values(), key=lambda item: (item.started_at, item.run_id))

    def page_runs(self, *, limit: int, cursor: str | None = None, status: str | None = None,
        agent_id: str | None = None, safety_state: str | None = None,
        started_after=None, started_before=None) -> tuple[list[AgentRunTrace], str | None]:
        items = [item for item in self.list_runs()[::-1]
            if (status is None or item.status.value == status)
            and (agent_id is None or item.agent_type == agent_id)
            and (safety_state is None or item.safety_state == safety_state)
            and (started_after is None or item.started_at >= started_after)
            and (started_before is None or item.started_at <= started_before)]
        if cursor:
            try: index = next(i for i, item in enumerate(items) if item.run_id == cursor) + 1
            except StopIteration as exc: raise ValueError("LAB_CURSOR_INVALID") from exc
            items = items[index:]
        page = items[:limit]
        return page, page[-1].run_id if len(items) > limit else None

    def put_step(self, trace: AgentStepTrace) -> None:
        self.step_traces[trace.id] = trace

    def transition_step(self, trace: AgentStepTrace, allowed_from: set[TraceStatus]) -> None:
        with self._lock:
            current = self.step_traces.get(trace.id)
            if current is None:
                raise ValueError("LAB_STEP_TRACE_NOT_FOUND")
            if current.status is trace.status and current.status is not TraceStatus.STARTED:
                return
            if current.status not in allowed_from:
                raise ValueError("LAB_STEP_TRACE_TRANSITION_INVALID")
            self.step_traces[trace.id] = trace

    def put_model_call(self, trace: ModelCallTrace) -> None:
        self.model_call_traces[trace.id] = trace

    def transition_model_call(self, trace: ModelCallTrace, allowed_from: set[TraceStatus]) -> None:
        with self._lock:
            current = self.model_call_traces.get(trace.id)
            if current is None:
                raise ValueError("LAB_MODEL_TRACE_NOT_FOUND")
            if current.status is trace.status and current.status is not TraceStatus.STARTED:
                return
            if current.status not in allowed_from:
                raise ValueError("LAB_MODEL_TRACE_TRANSITION_INVALID")
            self.model_call_traces[trace.id] = trace

    def list_steps(self, run_id: str | None = None) -> list[AgentStepTrace]:
        items = self.step_traces.values()
        return sorted(
            (item for item in items if run_id is None or item.run_id == run_id),
            key=lambda item: (item.started_at, item.id),
        )

    def list_model_calls(self, run_id: str | None = None) -> list[ModelCallTrace]:
        items = self.model_call_traces.values()
        return sorted(
            (item for item in items if run_id is None or item.run_id == run_id),
            key=lambda item: (item.started_at, item.id),
        )

    def put_tool_call(self, trace: ToolCallTrace) -> None: self.tool_call_traces[trace.id] = trace
    def transition_tool_call(self, trace: ToolCallTrace, allowed_from: set[TraceStatus]) -> None:
        with self._lock:
            current = self.tool_call_traces.get(trace.id)
            if current is None:
                raise ValueError("LAB_TOOL_TRACE_NOT_FOUND")
            if current.status is trace.status and current.status is not TraceStatus.STARTED:
                return
            if current.status not in allowed_from:
                raise ValueError("LAB_TOOL_TRACE_TRANSITION_INVALID")
            self.tool_call_traces[trace.id] = trace
    def put_safety_decision(self, trace: SafetyDecisionTrace) -> None: self.safety_decision_traces[trace.id] = trace
    def put_evidence_usage(self, trace: EvidenceUsageTrace) -> None: self.evidence_usage_traces[trace.id] = trace
    def list_tool_calls(self, run_id: str | None = None) -> list[ToolCallTrace]:
        return sorted((x for x in self.tool_call_traces.values() if run_id is None or x.run_id == run_id), key=lambda x: (x.started_at, x.id))
    def list_safety_decisions(self, run_id: str | None = None) -> list[SafetyDecisionTrace]:
        return sorted((x for x in self.safety_decision_traces.values() if run_id is None or x.run_id == run_id), key=lambda x: (x.decided_at, x.id))
    def list_evidence_usage(self, run_id: str | None = None) -> list[EvidenceUsageTrace]:
        return sorted((x for x in self.evidence_usage_traces.values() if run_id is None or x.run_id == run_id), key=lambda x: (x.recorded_at, x.id))

    def put_safety_report(self, item: SafetyReport) -> None:
        with self._lock:
            if item.id in self.safety_reports:
                raise ValueError("LAB_SAFETY_REPORT_ALREADY_EXISTS")
            self.safety_reports[item.id] = item

    def list_safety_reports(self) -> list[SafetyReport]:
        return sorted(self.safety_reports.values(), key=lambda x: (x.created_at, x.id))

    def put_outcome(self, item: OutcomeObservation) -> None:
        self.outcomes[item.id] = item

    def list_outcomes(self) -> list[OutcomeObservation]:
        return sorted(self.outcomes.values(), key=lambda x: (x.observed_at, x.id))

    def put_review(self, item: HumanReview) -> None:
        self.reviews[item.id] = item

    def list_reviews(self) -> list[HumanReview]:
        return sorted(self.reviews.values(), key=lambda x: (x.created_at, x.id))

    def put_rollup(self, item: MetricRollup) -> None:
        self.rollups[item.id] = item

    def list_rollups(self) -> list[MetricRollup]:
        return sorted(self.rollups.values(), key=lambda x: (x.bucket, x.id))

    def put_evaluation(self, item: EvaluationResult) -> None:
        with self._lock:
            existing = self.evaluations.get(item.id)
            if existing and existing != item:
                raise ValueError("LAB_EVALUATION_IMMUTABLE")
            self.evaluations[item.id] = item

    def list_evaluations(self) -> list[EvaluationResult]:
        return sorted(self.evaluations.values(), key=lambda x: (x.evaluated_at, x.id))

    def append_audit(self, item: AdminAuditEvent) -> bool:
        with self._lock:
            if item.id in self.audit_events:
                return False
            self.audit_events[item.id] = item
            return True

    def list_audit(self) -> list[AdminAuditEvent]:
        return sorted(self.audit_events.values(), key=lambda x: (x.occurred_at, x.id))

    def delete_owner_lab_data(self, owner: str) -> dict[str, int]:
        """Remove personal Lab material; aggregate rollups and admin audit stay anonymous."""
        counts: dict[str, int] = {}
        with self._lock:
            def delete_ids(values, ids) -> int:
                selected = list(ids)
                for entity_id in selected:
                    values.pop(entity_id, None)
                return len(selected)

            owned_run_ids = {key for key, value in self.run_traces.items() if value.owner_user_id == owner}
            owned_feedback_ids = {key for key, value in self.feedback.items() if value.owner_user_id == owner}
            owned_report_ids = {key for key, value in self.safety_reports.items() if value.owner_user_id == owner}
            for name, values in (
                ("responses", self.responses), ("feedback", self.feedback),
                ("run_traces", self.run_traces), ("safety_reports", self.safety_reports),
                ("outcomes", self.outcomes),
            ):
                ids = [key for key, value in values.items() if getattr(value, "owner_user_id", None) == owner]
                counts[name] = delete_ids(values, ids)
            review_ids = [key for key, value in self.reviews.items() if value.safety_report_id in owned_report_ids or value.run_id in owned_run_ids]
            counts["reviews"] = delete_ids(self.reviews, review_ids)
            comment_ids = [key for key in self.comments if key in owned_feedback_ids or key in owned_report_ids]
            counts["comments"] = delete_ids(self.comments, comment_ids)
            step_ids = {key for key, value in self.step_traces.items() if value.run_id in owned_run_ids}
            delete_ids(self.step_traces, step_ids)
            model_ids = {key for key, value in self.model_call_traces.items() if value.run_id in owned_run_ids}
            delete_ids(self.model_call_traces, model_ids)
            counts["steps"] = len(step_ids); counts["model_calls"] = len(model_ids)
            for name, trace_values in (("tool_calls", self.tool_call_traces), ("safety_decisions", self.safety_decision_traces), ("evidence_usage", self.evidence_usage_traces)):
                ids = [key for key, value in trace_values.items() if value.run_id in owned_run_ids]
                counts[name] = delete_ids(trace_values, ids)
        return counts
