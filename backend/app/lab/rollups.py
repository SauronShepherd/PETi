from __future__ import annotations

from datetime import UTC, datetime, timedelta

from .contracts import MetricRollup
from .enums import FeedbackValue, RollupGranularity, RufsState, TraceStatus
from .frustration import friction_index
from .metrics import METRIC_CATALOG, classify_rufs

ALLOWED_DIMENSIONS = frozenset({"environment", "deployment_id", "agent_id", "model_id", "provider", "outcome", "safety_state"})


def compute_core_rollups(repository, *, minimum_sample: int, now: datetime | None = None) -> list[MetricRollup]:
    now = now or datetime.now(UTC)
    all_runs = repository.list_runs()
    all_feedback = [item for item in repository.list_feedback() if item.removed_at is None]
    all_responses = [item for item in repository.list_responses() if item.deleted_at is None]
    all_calls = repository.list_model_calls()
    all_steps = repository.list_steps()
    all_events = repository.list_events()
    result: list[MetricRollup] = []
    windows = (
        (RollupGranularity.HOUR, now.replace(minute=0, second=0, microsecond=0)),
        (RollupGranularity.DAY, now.replace(hour=0, minute=0, second=0, microsecond=0)),
    )
    for granularity, start in windows:
        end = start + (timedelta(hours=1) if granularity is RollupGranularity.HOUR else timedelta(days=1))
        bucket = start.strftime("%Y-%m-%dT%H:00:00Z") if granularity is RollupGranularity.HOUR else start.strftime("%Y-%m-%d")
        runs = [item for item in all_runs if start <= item.started_at < end]
        run_ids = {item.run_id for item in runs}
        feedback = [item for item in all_feedback if start <= item.updated_at < end]
        responses = [item for item in all_responses if start <= item.published_at < end]
        calls = [item for item in all_calls if item.run_id in run_ids or start <= item.started_at < end]
        steps = [item for item in all_steps if item.run_id in run_ids]
        events = [item for item in all_events if start <= item.occurred_at < end]
        terminal_runs = [item for item in runs if item.status is not TraceStatus.STARTED]
        safe_states = {"SAFE_TO_DISPLAY", "REVIEW_REQUIRED", "SAFETY_ROUTED", "POLICY_BLOCKED"}
        feedback_by_run = {item.run_id: item for item in all_feedback if item.run_id in run_ids}
        rufs_pass = 0
        for run in runs:
            run_steps = [item for item in steps if item.run_id == run.run_id]
            claims = sum(item.claim_count for item in run_steps)
            grounded = sum(item.claim_count for item in run_steps if item.evidence_count > 0)
            state = classify_rufs(
                outcome=run.outcome or "UNKNOWN", safety_state=run.safety_state or "UNKNOWN",
                grounded_claims=grounded, total_claims=claims,
                feedback_value=getattr(feedback_by_run.get(run.run_id), "value", None),
            )
            rufs_pass += state.overall is RufsState.PASS
        claims = sum(item.claim_count for item in steps)
        grounded_claims = sum(item.claim_count for item in steps if item.evidence_count > 0)
        known_calls = sum(item.usage_status != "UNKNOWN" for item in calls)
        successful_calls = sum(item.status is TraceStatus.SUCCEEDED for item in calls)
        known_latencies = [item.latency_ms for item in calls if item.latency_ms is not None]
        selected_evidence = sum(item.evidence_count for item in steps)
        friction = friction_index(events, feedback)
        metrics = [
            ("run_completion", sum(item.status is TraceStatus.SUCCEEDED for item in terminal_runs), len(terminal_runs), len(terminal_runs)),
            ("helpfulness", sum(item.value is FeedbackValue.HELPED for item in feedback), len(feedback), len(feedback)),
            ("feedback_coverage", len(feedback), len(responses), len(responses)),
            ("safe_completion", sum(item.safety_state in safe_states for item in terminal_runs), len(terminal_runs), len(terminal_runs)),
            ("grounded_claim_rate", grounded_claims, claims, claims),
            ("known_usage_coverage", known_calls, len(calls), len(calls)),
            ("model_success_rate", successful_calls, len(calls), len(calls)),
            ("average_model_latency_ms", sum(known_latencies), len(known_latencies), len(known_latencies)),
            ("evidence_per_run", selected_evidence, len(runs), len(runs)),
            ("rufs", rufs_pass, len(runs), len(runs)),
            ("friction_index", friction["value"], 100, len(events) + len(feedback)),
        ]
        for name, numerator, denominator, sample_count in metrics:
            definition = METRIC_CATALOG[name]
            result.append(MetricRollup(
                f"{granularity.value}:{bucket}:{name}", bucket, granularity, name, {},
                numerator, denominator, sample_count,
                numerator / denominator if denominator else None,
                sample_count < minimum_sample,
                schema_version=definition.version,
            ))
    return result
