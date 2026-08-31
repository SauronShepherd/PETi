from datetime import UTC, datetime, timedelta

import pytest
from app.lab.contracts import (
    AgentRunTrace,
    AgentStepTrace,
    EvaluationResult,
    InteractionResponse,
    TelemetryEvent,
    TraceContext,
)
from app.lab.enums import (
    DataClassification,
    FeedbackReason,
    FeedbackValue,
    ResponseSourceType,
    ReviewSeverity,
    TraceStatus,
)
from app.lab.evaluations import CRITICAL_GATES, release_gate_decision, validate_evaluation
from app.lab.feedback import FeedbackService
from app.lab.frustration import friction_index
from app.lab.operations import LabOperationsService
from app.lab.queries import LabQueryService
from app.lab.repositories import InMemoryLabRepository
from app.lab.telemetry import TelemetryService


def response(owner="owner-1"):
    return InteractionResponse(owner, "hash", "interaction-1", ResponseSourceType.AGENT_RUN,
        "run-1", "SUCCEEDED", "SAFE_TO_DISPLAY", "deploy-1", id="response-1", run_id="run-1")


def test_safety_report_creates_review_without_exposing_description():
    repo = InMemoryLabRepository(); repo.create(response())
    service = LabOperationsService(repo, hash_secret="secret")
    report = service.safety_report("owner-1", response(), category="FALSE_REASSURANCE",
        severity=ReviewSeverity.HIGH, description="This looked unsafe")
    assert report.public()["severity"] == "HIGH"
    assert "description" not in report.public()
    assert repo.comments[report.id] == "This looked unsafe"
    assert repo.list_reviews()[0].safety_report_id == report.id
    with pytest.raises(ValueError, match="LAB_SAFETY_CATEGORY_INVALID"):
        service.safety_report("owner-1", response(), category="free text", severity=ReviewSeverity.LOW)


def test_retention_removes_expired_safety_report_description():
    repo = InMemoryLabRepository(); repo.create(response())
    now = datetime.now(UTC)
    service = LabOperationsService(repo, hash_secret="secret", retention_days=1)
    report = service.safety_report(
        "owner-1", response(), category="FALSE_REASSURANCE",
        severity=ReviewSeverity.HIGH, description="private report",
    )
    report.expires_at = now - timedelta(seconds=1)
    assert service.expire(now)["comments"] == 1
    assert report.id not in repo.comments


def test_outcome_rollups_friction_and_audit_have_bounded_dimensions():
    repo = InMemoryLabRepository(); repo.create(response())
    telemetry = TelemetryService(repo, hash_secret="secret")
    feedback = FeedbackService(repo, telemetry, hash_secret="secret")
    feedback.upsert("owner-1", "response-1", value=FeedbackValue.NOT_QUITE,
        reasons=[FeedbackReason.TOO_SLOW])
    service = LabOperationsService(repo, hash_secret="secret", minimum_sample=2)
    assert service.outcome("owner-1", response(), "ESCALATED_TO_VET").outcome_value == "ESCALATED_TO_VET"
    rollups = service.recompute_rollups(datetime(2026, 8, 31, 10, tzinfo=UTC))
    assert len(rollups) == 22 and all(not item.dimensions for item in rollups)
    assert {item.metric_name for item in rollups} >= {
        "safe_completion", "grounded_claim_rate", "known_usage_coverage",
        "model_success_rate", "average_model_latency_ms", "evidence_per_run",
        "rufs", "friction_index",
    }
    score = friction_index(repo.list_events(), repo.list_feedback())
    assert score["value"] == 37
    event = service.audit("admin-1", "LAB_RUN_VIEWED", "RUN", "run-1", "corr-1")
    assert event.actor_hash != "admin-1" and event.target_id_hash != "run-1"


def test_retention_and_owner_deletion_remove_personal_data_but_keep_audit_rollups():
    repo = InMemoryLabRepository(); item = response(); repo.create(item)
    telemetry = TelemetryService(repo, hash_secret="secret")
    feedback = FeedbackService(repo, telemetry, hash_secret="secret")
    saved = feedback.upsert("owner-1", item.id, value=FeedbackValue.HELPED,
        reasons=[FeedbackReason.CLEAR], comment="private")
    saved.updated_at = datetime.now(UTC) - timedelta(days=91)
    service = LabOperationsService(repo, hash_secret="secret", retention_days=90)
    service.recompute_rollups(); service.audit("admin", "TEST", "LAB", None, "corr")
    assert service.expire()["comments"] == 1
    counts = repo.delete_owner_lab_data("owner-1")
    assert counts["responses"] == 1 and counts["feedback"] == 1
    assert repo.list_rollups() and repo.list_audit()


def test_telemetry_expiry_removes_only_expired_events():
    repo = InMemoryLabRepository(); now = datetime.now(UTC)
    repo.append(TelemetryEvent("run_started", "LOCAL", DataClassification.TEST, "c1", id="old", expires_at=now - timedelta(seconds=1)))
    repo.append(TelemetryEvent("run_started", "LOCAL", DataClassification.TEST, "c2", id="new", expires_at=now + timedelta(days=1)))
    assert LabOperationsService(repo, hash_secret="secret").expire(now)["events"] == 1
    assert [event.id for event in repo.list_events()] == ["new"]


def test_run_pagination_is_stable_and_rejects_unknown_cursor():
    repo = InMemoryLabRepository(); instant = datetime.now(UTC)
    for index in range(3):
        repo.put_run(AgentRunTrace(f"run-{index}", f"i-{index}", f"c-{index}", "owner", "hash", "pet",
            "ORCHESTRATOR", "deploy", "LOCAL", DataClassification.TEST, TraceStatus.SUCCEEDED,
            started_at=instant + timedelta(seconds=index)))
    first, cursor = repo.page_runs(limit=2)
    second, next_cursor = repo.page_runs(limit=2, cursor=cursor)
    assert [item.run_id for item in first] == ["run-2", "run-1"]
    assert [item.run_id for item in second] == ["run-0"] and next_cursor is None
    with pytest.raises(ValueError, match="LAB_CURSOR_INVALID"): repo.page_runs(limit=2, cursor="missing")


def test_evaluation_registry_blocks_release_until_every_critical_gate_passes():
    repo = InMemoryLabRepository()
    assert release_gate_decision(repo.list_evaluations())["decision"] == "BLOCK"
    failed = EvaluationResult(
        "eval-fail", "PETI_CHECK", "deploy-1", "release-1", "FAIL",
        {gate: "FAIL" if gate == "false_reassurance" else "PASS" for gate in CRITICAL_GATES},
        {"helpfulness": 0.9}, "manifest-1",
    )
    repo.put_evaluation(validate_evaluation(failed))
    assert release_gate_decision(repo.list_evaluations())["reason"] == "CRITICAL_GATE_FAILED"
    passed = EvaluationResult(
        "eval-pass", "PETI_CHECK", "deploy-2", "release-2", "PASS",
        {gate: "PASS" for gate in CRITICAL_GATES}, {"helpfulness": 0.91}, "manifest-2",
        evaluated_at=failed.evaluated_at + timedelta(seconds=1),
    )
    repo.put_evaluation(validate_evaluation(passed))
    assert release_gate_decision(repo.list_evaluations())["decision"] == "ALLOW"
    with pytest.raises(ValueError, match="LAB_EVALUATION_PASS_CONTRADICTS_GATE"):
        validate_evaluation(EvaluationResult(
            "invalid", "PETI_CHECK", "deploy", "release", "PASS",
            {gate: "FAIL" for gate in CRITICAL_GATES}, {}, "manifest",
        ))


def test_health_reports_observability_completeness_orphans_and_rollup_lag():
    repo = InMemoryLabRepository()
    telemetry = TelemetryService(repo, hash_secret="secret")
    service = LabOperationsService(repo, hash_secret="secret")
    run = AgentRunTrace(
        "run-health", "interaction", "correlation", "owner", "hash", None,
        "ORCHESTRATOR", "deploy", "LOCAL", DataClassification.TEST,
        TraceStatus.SUCCEEDED, response_id="response-health",
    )
    repo.put_run(run)
    repo.put_step(AgentStepTrace(
        "step-health", run.run_id, "plan", "ORCHESTRATOR", "1", "1",
        TraceStatus.SUCCEEDED, datetime.now(UTC),
    ))
    telemetry.emit("run_started", context=TraceContext(
        "correlation", "interaction", "deploy", "LOCAL",
        DataClassification.TEST, run_id=run.run_id, owner_user_id="owner",
    ), properties={"agent_type": "ORCHESTRATOR"})
    service.recompute_rollups()
    health = LabQueryService(repo, minimum_sample=1, telemetry=telemetry).health()
    assert health["trace_completeness_rate"]["value"] == 1.0
    assert health["orphan_trace_count"] == 0
    assert health["rollup_lag_seconds"] is not None
    assert health["telemetry_events_attempted"] == 1
