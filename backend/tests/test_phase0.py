from datetime import UTC, datetime

import pytest
from app.config.settings import Environment, Settings
from app.main import app
from app.services.pipeline import AnalysisOrchestrator
from app.services.ports import FakeAIProvider, FakeClock, FakeIdGenerator, FakeScenario
from fastapi.testclient import TestClient


def test_health_and_correlation():
    c = TestClient(app)
    r = c.get("/health/live")
    assert r.status_code == 200
    assert r.headers["X-Correlation-ID"]
    assert c.get("/health/ready").json()["status"] == "ready"


def test_unknown_route_is_safe():
    r = TestClient(app).get("/v1/nope")
    assert r.status_code == 404
    assert "traceback" not in r.text.lower()


def test_config_fails_closed():
    try:
        Settings(environment=Environment.PRODUCTION).validate_startup()
        assert False
    except ValueError:
        pass


def test_fakes_are_deterministic():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    assert FakeClock(t).now() == t
    ids = FakeIdGenerator()
    assert ids.new_id() == "fake-1"
    assert FakeAIProvider().analyze("x")["status"] == "candidate"


def test_pipeline_order_and_safety_stage():
    seen = []

    def stage(name):
        return lambda x: seen.append(name) or x

    AnalysisOrchestrator(
        *(stage(x) for x in ("prepare", "ai", "validate", "guardrails", "safety", "persist"))
    ).run(None)
    assert seen == ["prepare", "ai", "validate", "guardrails", "safety", "persist"]


def test_fake_scenarios_are_explicit():
    for s in FakeScenario:
        if s is not FakeScenario.SUCCESS:
            try:
                FakeAIProvider(s).analyze(None)
                assert False
            except RuntimeError as e:
                assert str(e) == s.value


def test_local_zero_cost_policy_rejects_real_cloud_storage_and_ai():
    with pytest.raises(ValueError, match="ZERO_COST_POLICY"):
        Settings(storage_mode="FIRESTORE").validate_startup()
    with pytest.raises(ValueError, match="ZERO_COST_POLICY"):
        Settings(ai_provider="GEMINI").validate_startup()


@pytest.mark.parametrize("environment", [Environment.STAGING, Environment.PRODUCTION])
def test_release_environments_reject_ephemeral_memory_storage(environment):
    with pytest.raises(ValueError, match="durable Firestore"):
        Settings(
            environment=environment,
            project_id="peti-release",
            auth_mode="FIREBASE",
            media_bucket="peti-media",
            tasks_project_id="peti-release",
            analysis_worker_url="https://worker.example",
            ai_provider="GEMINI",
        ).validate_startup()


def test_production_rejects_peti_check_without_external_release_certificate():
    with pytest.raises(ValueError, match="externally certified"):
        Settings(
            environment=Environment.PRODUCTION,
            project_id="peti-release",
            auth_mode="FIREBASE",
            storage_mode="FIRESTORE",
            media_bucket="peti-media",
            tasks_project_id="peti-release",
            analysis_worker_url="https://worker.example",
            ai_provider="GEMINI",
            peti_check_enabled=True,
        ).validate_startup()


def test_adk_requires_agent_runtime():
    with pytest.raises(ValueError, match="ADK requires PETI_AGENT_RUNTIME_ENABLED"):
        Settings(agent_adk_enabled=True).validate_startup()


def test_adk_rejects_fake_provider():
    with pytest.raises(ValueError, match="ADK requires a configured model provider"):
        Settings(agent_adk_enabled=True, agent_runtime_enabled=True).validate_startup()
