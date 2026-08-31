from datetime import UTC, datetime

import pytest
from app.auth.models import AuthenticatedPrincipal
from app.lab.contracts import (
    AgentRunTrace,
    AgentStepTrace,
    InteractionResponse,
    ModelCallTrace,
    TraceContext,
)
from app.lab.enums import (
    DataClassification,
    FeedbackReason,
    FeedbackValue,
    LabPermission,
    ResponseSourceType,
    RufsState,
    TraceStatus,
)
from app.lab.feedback import FeedbackService
from app.lab.hashing import feedback_id, owner_hash, owner_hash_matches
from app.lab.metrics import classify_rufs, proportion
from app.lab.permissions import permissions_for, require_permission
from app.lab.queries import LabQueryService
from app.lab.repositories import InMemoryLabRepository
from app.lab.telemetry import TelemetryService


def context(owner: str = "owner-1") -> TraceContext:
    return TraceContext(
        correlation_id="corr-1",
        interaction_id="interaction-1",
        run_id="run-1",
        owner_user_id=owner,
        pet_id="pet-1",
        agent_id="ORCHESTRATOR",
        deployment_id="test-deployment",
        environment="LOCAL",
        data_classification=DataClassification.TEST,
    )


def response(owner: str = "owner-1") -> InteractionResponse:
    return InteractionResponse(
        id="response-1",
        owner_user_id=owner,
        owner_hash=owner_hash(owner, "secret"),
        interaction_id="interaction-1",
        run_id="run-1",
        source_type=ResponseSourceType.AGENT_RUN,
        source_id="run-1",
        outcome="ANSWERED",
        safety_state="SAFE_TO_DISPLAY",
        deployment_id="test-deployment",
        environment="LOCAL",
        data_classification=DataClassification.TEST,
        published_at=datetime.now(UTC),
    )


def test_telemetry_is_allowlisted_idempotent_and_pseudonymous():
    repository = InMemoryLabRepository()
    service = TelemetryService(repository, hash_secret="secret")
    first = service.emit(
        "run_created",
        context=context(),
        properties={"agent_type": "ORCHESTRATOR", "goal_type": "REVIEW_EVIDENCE"},
        event_id="event-1",
    )
    duplicate = service.emit(
        "run_created",
        context=context(),
        properties={"agent_type": "ORCHESTRATOR"},
        event_id="event-1",
    )
    assert first is not None and duplicate is not None
    assert len(repository.events) == 1
    assert first.actor_id_hash == owner_hash("owner-1", "secret")
    assert "owner-1" not in str(first.public())


def test_telemetry_rejects_unknown_or_sensitive_properties():
    service = TelemetryService(InMemoryLabRepository(), hash_secret="secret")
    with pytest.raises(ValueError, match="LAB_EVENT_PROPERTIES_NOT_ALLOWED"):
        service.emit("run_created", context=context(), properties={"email": "a@example.test"})
    with pytest.raises(ValueError, match="LAB_EVENT_NOT_ALLOWED"):
        service.emit("made_up", context=context())


def test_feedback_create_update_remove_and_comment_lifecycle():
    store = InMemoryLabRepository()
    store.create(response())
    telemetry = TelemetryService(store, hash_secret="secret")
    service = FeedbackService(store, telemetry, hash_secret="secret")

    created = service.upsert(
        "owner-1",
        "response-1",
        value=FeedbackValue.HELPED,
        reasons=[FeedbackReason.CLEAR],
        comment="  Muy claro.  ",
        locale="es",
    )
    assert created.revision == 1
    assert store.comments[created.id] == "Muy claro."

    updated = service.upsert(
        "owner-1",
        "response-1",
        value=FeedbackValue.NOT_QUITE,
        reasons=[FeedbackReason.NO_CLEAR_NEXT_STEP],
    )
    assert updated.revision == 2
    assert updated.created_at == created.created_at
    assert created.id not in store.comments

    removed = service.remove("owner-1", "response-1")
    assert removed.revision == 3
    assert removed.removed_at is not None
    assert [event.event_name for event in store.list_events()] == [
        "feedback_submitted",
        "feedback_updated",
        "feedback_removed",
    ]


def test_feedback_enforces_ownership_eligibility_and_reason_polarity():
    store = InMemoryLabRepository()
    store.create(response())
    service = FeedbackService(
        store,
        TelemetryService(store, hash_secret="secret"),
        hash_secret="secret",
    )
    with pytest.raises(ValueError, match="LAB_RESPONSE_NOT_FOUND"):
        service.upsert("other", "response-1", value="HELPED")
    with pytest.raises(ValueError, match="LAB_FEEDBACK_REASON_VALUE_MISMATCH"):
        service.upsert(
            "owner-1", "response-1", value="HELPED", reasons=["TOO_GENERIC"]
        )


def test_hashes_are_stable_and_scoped():
    assert owner_hash("owner-1", "secret") == owner_hash("owner-1", "secret")
    assert owner_hash("owner-1", "secret") != owner_hash("owner-1", "other")
    assert feedback_id("owner-1", "response-1") == feedback_id("owner-1", "response-1")
    assert len(feedback_id("owner-1", "response-1")) == 40


def test_owner_hash_rotation_accepts_active_previous_and_explicit_legacy_keys():
    keys = {"v2": "new-secret", "v1": "old-secret"}
    current = owner_hash("owner-1", keys["v2"], key_id="v2")
    previous = owner_hash("owner-1", keys["v1"], key_id="v1")
    legacy = owner_hash("owner-1", keys["v1"])
    assert owner_hash_matches("owner-1", current, keys)
    assert owner_hash_matches("owner-1", previous, keys)
    assert owner_hash_matches("owner-1", legacy, keys, legacy_secret=keys["v1"])
    assert not owner_hash_matches("owner-2", current, keys)
    assert not owner_hash_matches("owner-1", "retired:" + "0" * 64, keys)


def test_proportion_returns_wilson_interval_and_marks_small_samples():
    metric = proportion(8, 10)
    assert metric.value == 0.8
    assert metric.low is not None and metric.low < metric.value
    assert metric.high is not None and metric.high > metric.value
    assert metric.preliminary is True
    assert proportion(0, 0).value is None


def test_rufs_does_not_treat_missing_feedback_as_useful():
    unknown = classify_rufs(
        outcome="ANSWERED",
        safety_state="SAFE_TO_DISPLAY",
        grounded_claims=2,
        total_claims=2,
        feedback_value=None,
    )
    assert unknown.useful is RufsState.UNKNOWN
    assert unknown.overall is RufsState.UNKNOWN

    passed = classify_rufs(
        outcome="ANSWERED",
        safety_state="SAFE_TO_DISPLAY",
        grounded_claims=2,
        total_claims=2,
        feedback_value=FeedbackValue.HELPED,
    )
    assert passed.overall is RufsState.PASS


def test_agent_and_model_helpfulness_expose_scalar_and_statistical_detail():
    store = InMemoryLabRepository()
    store.create(response())
    store.put_run(AgentRunTrace(
        "run-1", "interaction-1", "corr-1", "owner-1", "hash", "pet-1",
        "ORCHESTRATOR", "deploy", "LOCAL", DataClassification.TEST,
        TraceStatus.SUCCEEDED,
    ))
    store.put_model_call(ModelCallTrace(
        "call-1", "run-1", "step-1", "ORCHESTRATOR", "corr-1", "google",
        "gemini-test", TraceStatus.SUCCEEDED, datetime.now(UTC),
    ))
    FeedbackService(
        store, TelemetryService(store, hash_secret="secret"), hash_secret="secret"
    ).upsert("owner-1", "response-1", value=FeedbackValue.HELPED,
             reasons=[FeedbackReason.CLEAR])

    queries = LabQueryService(store, minimum_sample=1)
    agent = next(item for item in queries.agents() if item["agent_id"] == "ORCHESTRATOR")
    model = queries.models()[0]
    assert agent["helpfulness"] == 1.0
    assert agent["helpfulness_metric"]["denominator"] == 1
    assert model["helpfulness"] == 1.0
    assert model["helpfulness_metric"]["denominator"] == 1


def test_trace_state_transitions_are_compare_and_set_and_terminal_is_idempotent():
    store = InMemoryLabRepository(); now = datetime.now(UTC)
    run = AgentRunTrace("run-cas", "interaction", "corr", "owner", "hash", None,
        "ORCHESTRATOR", "deploy", "LOCAL", DataClassification.TEST)
    step = AgentStepTrace("step-cas", run.run_id, "plan", "ORCHESTRATOR", "1", "1",
        TraceStatus.STARTED, now)
    call = ModelCallTrace("call-cas", run.run_id, step.id, "ORCHESTRATOR", "corr",
        "FAKE", "fake", TraceStatus.STARTED, now)
    store.put_run(run); store.put_step(step); store.put_model_call(call)
    completed_run = AgentRunTrace(**{**run.__dict__, "status": TraceStatus.SUCCEEDED})
    completed_step = AgentStepTrace(**{**step.__dict__, "status": TraceStatus.SUCCEEDED})
    completed_call = ModelCallTrace(**{**call.__dict__, "status": TraceStatus.SUCCEEDED})
    store.transition_run(completed_run, {TraceStatus.STARTED})
    store.transition_step(completed_step, {TraceStatus.STARTED})
    store.transition_model_call(completed_call, {TraceStatus.STARTED})
    store.transition_run(completed_run, {TraceStatus.STARTED})
    with pytest.raises(ValueError, match="LAB_RUN_TRACE_TRANSITION_INVALID"):
        store.transition_run(AgentRunTrace(**{**run.__dict__, "status": TraceStatus.FAILED}), {TraceStatus.STARTED})


def test_permissions_are_fail_closed_and_environment_scoped():
    admin = AuthenticatedPrincipal("f1", "u1", "ADMIN", True, True)
    tester = AuthenticatedPrincipal("f2", "u2", "INTERNAL_TEST", True, True)
    customer = AuthenticatedPrincipal("f3", "u3", "CUSTOMER", False, False)
    assert LabPermission.VIEW_USER_CONTENT in permissions_for(admin, "PRODUCTION")
    assert LabPermission.VIEW_TRACES in permissions_for(tester, "STAGING")
    assert not permissions_for(tester, "PRODUCTION")
    with pytest.raises(PermissionError, match="LAB_PERMISSION_REQUIRED"):
        require_permission(customer, LabPermission.VIEW_AGGREGATES, "LOCAL")
