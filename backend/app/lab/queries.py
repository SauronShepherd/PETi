from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from .enums import FeedbackValue, RufsState
from .evaluations import CRITICAL_GATES, release_gate_decision
from .frustration import friction_index
from .metrics import classify_rufs, proportion


def _public_dataclass(item: Any) -> dict[str, Any]:
    data = asdict(item)
    for key, value in list(data.items()):
        if hasattr(value, "value"):
            data[key] = value.value
    data.pop("owner_user_id", None)
    data.pop("owner_hash", None)
    return data


class LabQueryService:
    def __init__(self, repository, *, minimum_sample: int = 30, telemetry=None) -> None:
        self.repository = repository
        self.minimum_sample = minimum_sample
        self.telemetry = telemetry

    @staticmethod
    def _metric(value) -> dict[str, Any]:
        return {
            "value": value.value,
            "numerator": value.numerator,
            "denominator": value.denominator,
            "ci95": {"low": value.low, "high": value.high},
            "preliminary": value.preliminary,
        }

    def overview(self) -> dict[str, Any]:
        runs = self.repository.list_runs()
        feedback = [item for item in self.repository.list_feedback() if item.removed_at is None]
        responses = [item for item in self.repository.list_responses() if item.deleted_at is None]
        positive = sum(1 for item in feedback if item.value is FeedbackValue.HELPED)
        completed = sum(1 for item in runs if item.status.value == "SUCCEEDED")
        safe = sum(
            1
            for item in runs
            if item.safety_state in {"SAFE_TO_DISPLAY", "REVIEW_REQUIRED", "SAFETY_ROUTED", "POLICY_BLOCKED"}
        )
        run_states = Counter(item.status.value for item in runs)
        agent_counts = Counter(item.agent_type for item in runs)
        models = Counter(
            f"{item.provider}/{item.model_id}" for item in self.repository.list_model_calls()
        )
        feedback_by_run = {item.run_id: item for item in feedback}
        all_steps = self.repository.list_steps()
        rufs_pass = 0
        for run in runs:
            steps = [item for item in all_steps if item.run_id == run.run_id]
            claims = sum(item.claim_count for item in steps)
            grounded = sum(item.claim_count for item in steps if item.evidence_count > 0)
            classification = classify_rufs(
                outcome=run.outcome or "UNKNOWN", safety_state=run.safety_state or "UNKNOWN",
                grounded_claims=grounded, total_claims=claims,
                feedback_value=getattr(feedback_by_run.get(run.run_id), "value", None),
            )
            rufs_pass += classification.overall is RufsState.PASS
        metric_values = {
            "run_completion": self._metric(proportion(completed, len(runs), minimum_sample=self.minimum_sample)),
            "helpfulness": self._metric(proportion(positive, len(feedback), minimum_sample=self.minimum_sample)),
            "feedback_coverage": self._metric(proportion(len(feedback), len(responses), minimum_sample=self.minimum_sample)),
            "safe_completion": self._metric(proportion(safe, len(runs), minimum_sample=self.minimum_sample)),
            "rufs": self._metric(proportion(rufs_pass, len(runs), minimum_sample=self.minimum_sample)),
            "grounded_claim_rate": self._metric(proportion(
                sum(item.claim_count for item in all_steps if item.evidence_count > 0),
                sum(item.claim_count for item in all_steps),
                minimum_sample=self.minimum_sample,
            )),
        }
        latest_rollups = {}
        for item in self.repository.list_rollups():
            if item.granularity.value == "HOUR" and not item.dimensions:
                latest_rollups[item.metric_name] = item
        for name, item in latest_rollups.items():
            if name in metric_values:
                metric_values[name] = self._metric(proportion(item.numerator, item.denominator, minimum_sample=self.minimum_sample))
                metric_values[name]["source"] = "ROLLUP"
                metric_values[name]["bucket"] = item.bucket
        metric_values["grounded"] = metric_values["grounded_claim_rate"]
        return {
            "schema_version": "1.0.0",
            "run_count": len(runs),
            "response_count": len(responses),
            "feedback_count": len(feedback),
            "metrics": metric_values,
            "runs_by_state": dict(sorted(run_states.items())),
            "runs_by_agent": dict(sorted(agent_counts.items())),
            "model_calls": dict(sorted(models.items())),
            "friction": friction_index(self.repository.list_events(), feedback),
            "rollup_count": len(self.repository.list_rollups()),
            "data_freshness_at": max(
                (item.computed_at for item in self.repository.list_rollups()), default=None
            ),
        }

    def list_runs(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return [_public_dataclass(item) for item in self.repository.list_runs()[-limit:][::-1]]

    def page_runs(
        self,
        *,
        limit: int = 100,
        cursor: str | None = None,
        model_id: str | None = None,
        feedback_value: str | None = None,
        min_duration_ms: int | None = None,
        sort: str = "STARTED_DESC",
        **filters,
    ) -> tuple[list[dict[str, Any]], str | None]:
        if model_id is None and feedback_value is None and min_duration_ms is None and sort == "STARTED_DESC":
            items, next_cursor = self.repository.page_runs(
                limit=limit, cursor=cursor, **filters
            )
            return [_public_dataclass(item) for item in items], next_cursor

        # Cross-entity filters are evaluated over a bounded, date-filtered candidate
        # window. The default path remains an indexed cursor query.
        candidates, _ = self.repository.page_runs(limit=1000, cursor=None, **filters)
        if model_id is not None:
            model_run_ids = {
                item.run_id for item in self.repository.list_model_calls()
                if item.model_id == model_id
            }
            candidates = [item for item in candidates if item.run_id in model_run_ids]
        if feedback_value is not None:
            feedback_run_ids = {
                item.run_id for item in self.repository.list_feedback()
                if item.removed_at is None and item.value.value == feedback_value
            }
            candidates = [item for item in candidates if item.run_id in feedback_run_ids]
        if min_duration_ms is not None:
            candidates = [
                item for item in candidates
                if item.duration_ms is not None and item.duration_ms >= min_duration_ms
            ]
        candidates.sort(
            key=lambda item: (item.started_at, item.run_id),
            reverse=sort == "STARTED_DESC",
        )
        if cursor:
            try:
                offset = next(
                    index for index, item in enumerate(candidates)
                    if item.run_id == cursor
                ) + 1
            except StopIteration as exc:
                raise ValueError("LAB_CURSOR_INVALID") from exc
            candidates = candidates[offset:]
        items = candidates[:limit]
        next_cursor = items[-1].run_id if len(candidates) > limit and items else None
        return [_public_dataclass(item) for item in items], next_cursor

    def run_detail(self, run_id: str, *, include_content: bool = False) -> dict[str, Any]:
        run = self.repository.get_run(run_id)
        if not run:
            raise ValueError("LAB_RUN_NOT_FOUND")
        response = next(
            (item for item in self.repository.list_responses() if item.run_id == run_id), None
        )
        feedback = next(
            (item for item in self.repository.list_feedback() if item.run_id == run_id), None
        )
        result = {
            "run": _public_dataclass(run),
            "steps": [
                _public_dataclass(item) for item in self.repository.list_steps(run_id)
            ],
            "model_calls": [
                _public_dataclass(item) for item in self.repository.list_model_calls(run_id)
            ],
            "tool_calls": [_public_dataclass(item) for item in self.repository.list_tool_calls(run_id)],
            "safety_decisions": [_public_dataclass(item) for item in self.repository.list_safety_decisions(run_id)],
            "evidence_usage": [_public_dataclass(item) for item in self.repository.list_evidence_usage(run_id)],
            "response": response.public() if response else None,
            "feedback": feedback.public() if feedback and not feedback.removed_at else None,
        }
        if include_content:
            result["content"] = {
                "available": bool(response and response.content_ref),
                "reference": response.content_ref if response else None,
            }
        return result

    def agents(self) -> list[dict[str, Any]]:
        from app.agents.roster import AGENT_CAPABILITIES, AgentType

        runs = self.repository.list_runs()
        feedback_by_run = {item.run_id: item for item in self.repository.list_feedback() if item.removed_at is None}
        result = []
        for agent in AgentType:
            agent_runs = [run for run in runs if run.agent_type == agent.value]
            rated_runs = [run for run in agent_runs if run.run_id in feedback_by_run]
            helpfulness = proportion(
                sum(feedback_by_run[run.run_id].value is FeedbackValue.HELPED for run in rated_runs),
                len(rated_runs),
                minimum_sample=self.minimum_sample,
            )
            result.append({
                "agent_id": agent.value,
                "capabilities": sorted(AGENT_CAPABILITIES[agent]),
                "run_count": len(agent_runs),
                "activity_status": (
                    "ACTIVE" if agent_runs else "NO_ACTIVITY"
                ),
                "helpfulness": helpfulness.value,
                "helpfulness_metric": self._metric(helpfulness),
            })
        return result

    def models(self) -> list[dict[str, Any]]:
        calls = self.repository.list_model_calls()
        feedback_by_run = {item.run_id: item for item in self.repository.list_feedback() if item.removed_at is None}
        keys = sorted({(item.provider, item.model_id) for item in calls})
        result = []
        for provider, model in keys:
            model_calls = [item for item in calls if item.provider == provider and item.model_id == model]
            rated_calls = [item for item in model_calls if item.run_id in feedback_by_run]
            helpfulness = proportion(
                sum(feedback_by_run[item.run_id].value is FeedbackValue.HELPED for item in rated_calls),
                len(rated_calls),
                minimum_sample=self.minimum_sample,
            )
            known_latencies = [item.latency_ms for item in model_calls if item.latency_ms is not None]
            result.append({
                "provider": provider,
                "model_id": model,
                "call_count": len(model_calls),
                "input_tokens": sum(
                    item.input_tokens or 0 for item in model_calls
                ),
                "output_tokens": sum(
                    item.output_tokens or 0 for item in model_calls
                ),
                "unknown_usage_count": sum(
                    1 for item in model_calls if item.usage_status == "UNKNOWN"
                ),
                "average_latency_ms": (
                    round(sum(known_latencies) / len(known_latencies)) if known_latencies else None
                ),
                "helpfulness": helpfulness.value,
                "helpfulness_metric": self._metric(helpfulness),
            })
        return result

    def feedback(self, *, limit: int = 100, include_comment: bool = False) -> list[dict[str, Any]]:
        result = []
        for item in self.repository.list_feedback()[-limit:][::-1]:
            if item.removed_at is not None:
                continue
            public = item.public()
            if include_comment:
                public["comment"] = self.repository.get_comment(item.id)
            result.append(public)
        return result

    def evidence_metrics(self) -> dict[str, Any]:
        steps = self.repository.list_steps()
        selected = sum(item.evidence_count for item in steps)
        grounded_claims = sum(item.claim_count for item in steps if item.evidence_count > 0)
        claims = sum(item.claim_count for item in steps)
        return {
            "selected_evidence_count": selected,
            "claim_count": claims,
            "grounded_claim_count": grounded_claims,
            "grounded_claim_rate": self._metric(
                proportion(grounded_claims, claims, minimum_sample=self.minimum_sample)
            ),
            "modalities": {"IMAGE": 0, "VIDEO": 0, "AUDIO": 0, "DOCUMENT": 0},
            "modality_coverage": "UNKNOWN",
        }

    def safety(self) -> dict[str, Any]:
        runs = self.repository.list_runs()
        review = [item for item in runs if item.safety_state == "REVIEW_REQUIRED"]
        gate_decision = release_gate_decision(self.repository.list_evaluations())
        reports = self.repository.list_safety_reports()
        reviews = self.repository.list_reviews()
        return {
            "review_required_count": len(review),
            "report_count": len(reports),
            "open_review_count": sum(item.status.value != "RESOLVED" for item in reviews),
            "items": [_public_dataclass(item) for item in reviews[-100:][::-1]],
            "critical_gates": [
                {"gate": gate, "status": gate_decision["critical_gates"][gate]}
                for gate in CRITICAL_GATES
            ],
            "release_decision": gate_decision,
        }

    def evaluations(self) -> dict[str, Any]:
        items = self.repository.list_evaluations()
        return {
            "items": [_public_dataclass(item) for item in items[-100:][::-1]],
            "release_decision": release_gate_decision(items),
        }

    def performance(self) -> dict[str, Any]:
        runs = self.repository.list_runs()
        calls = self.repository.list_model_calls()
        known_input = [item.input_tokens for item in calls if item.input_tokens is not None]
        known_output = [item.output_tokens for item in calls if item.output_tokens is not None]
        latencies = [item.latency_ms for item in calls if item.latency_ms is not None]
        return {
            "run_count": len(runs),
            "model_call_count": len(calls),
            "input_tokens": sum(known_input),
            "output_tokens": sum(known_output),
            "unknown_usage_count": sum(1 for item in calls if item.usage_status == "UNKNOWN"),
            "known_usage_coverage": self._metric(proportion(
                sum(item.usage_status != "UNKNOWN" for item in calls), len(calls),
                minimum_sample=self.minimum_sample,
            )),
            "model_success_rate": self._metric(proportion(
                sum(item.status.value == "SUCCEEDED" for item in calls), len(calls),
                minimum_sample=self.minimum_sample,
            )),
            "average_model_latency_ms": (
                round(sum(latencies) / len(latencies)) if latencies else None
            ),
            "estimated_cost_microunits": None,
            "cost_status": "UNKNOWN",
        }

    def health(self) -> dict[str, Any]:
        events = self.repository.list_events()
        runs = self.repository.list_runs()
        run_ids = {item.run_id for item in runs}
        steps = self.repository.list_steps()
        calls = self.repository.list_model_calls()
        tools = self.repository.list_tool_calls()
        safety = self.repository.list_safety_decisions()
        evidence = self.repository.list_evidence_usage()
        terminal = [item for item in runs if item.status.value != "STARTED"]
        complete = sum(
            bool(item.response_id) and any(step.run_id == item.run_id for step in steps)
            for item in terminal
        )
        orphan_count = sum(
            item.run_id not in run_ids
            for collection in (steps, calls, tools, safety, evidence)
            for item in collection
            if item.run_id is not None
        )
        rollups = self.repository.list_rollups()
        latest_rollup = max((item.computed_at for item in rollups), default=None)
        now = datetime.now(UTC)
        return {
            "status": "DEGRADED" if orphan_count else "OK",
            "telemetry_event_count": len(events),
            "trace_count": len(runs),
            "model_call_trace_count": len(calls),
            "latest_event_at": events[-1].occurred_at if events else None,
            "data_freshness": "CURRENT" if events else "NO_DATA",
            "telemetry_events_attempted": getattr(self.telemetry, "attempted_event_count", 0),
            "telemetry_events_written": getattr(self.telemetry, "written_event_count", 0),
            "telemetry_events_dropped": getattr(self.telemetry, "dropped_event_count", 0),
            "invalid_event_count": getattr(self.telemetry, "invalid_event_count", 0),
            "telemetry_write_failure_count": getattr(self.telemetry, "write_failure_count", 0),
            "trace_completeness_rate": self._metric(proportion(
                complete, len(terminal), minimum_sample=self.minimum_sample
            )),
            "orphan_trace_count": orphan_count,
            "rollup_lag_seconds": (
                max(0, round((now - latest_rollup).total_seconds()))
                if latest_rollup else None
            ),
            "latest_rollup_at": latest_rollup,
        }

    def audit(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return [_public_dataclass(item) for item in self.repository.list_audit()[-limit:][::-1]]
