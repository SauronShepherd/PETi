from app.agent_runtime.execution import AgentExecutionService
from app.agents.contracts import AgentOrchestrator
from app.ai.providers.fake import FakeAIProvider
from app.domain.users import UserRole
from app.lab.enums import DataClassification
from app.lab.feedback import FeedbackService
from app.lab.operations import LabOperationsService
from app.lab.queries import LabQueryService
from app.lab.repositories import InMemoryLabRepository
from app.lab.telemetry import TelemetryService
from app.lab.tracing import LabTraceService
from app.main import app
from fastapi.testclient import TestClient


class Media:
    def __init__(self):
        self.items: list = []
        self.version = "1.0.0"


def configured_lab():
    repository = InMemoryLabRepository()
    telemetry = TelemetryService(repository, hash_secret="test-secret")
    tracing = LabTraceService(
        repository,
        telemetry,
        hash_secret="test-secret",
        environment="LOCAL",
        deployment_id="test-deployment",
    )
    return repository, telemetry, tracing


def test_agent_execution_publishes_trace_and_feedback_eligible_response():
    repository, _, tracing = configured_lab()
    runs = AgentOrchestrator()
    run = runs.create_run(
        "owner-a",
        "Review evidence",
        "pet-a",
        deployment_id="test-deployment",
    )
    result = AgentExecutionService(runs, FakeAIProvider(), lab=tracing).execute(
        "owner-a", run.id, Media()
    )
    assert result["response_id"]
    assert result["steps"][-1]["final"]["feedback_eligible"] is True
    detail = LabQueryService(repository).run_detail(run.id)
    assert detail["run"]["status"] == "SUCCEEDED"
    assert [step["step_id"] for step in detail["steps"]] == [
        "plan",
        "evidence-intake",
        "peti-check",
        "safety-review",
        "care-report",
    ]
    assert detail["response"]["id"] == result["response_id"]
    assert len(detail["model_calls"]) == 1
    assert detail["model_calls"][0]["provider"] == "FAKE"
    assert detail["model_calls"][0]["model_id"] == "fake-platform-smoke-v1"
    assert detail["model_calls"][0]["input_tokens"] == 12
    assert detail["model_calls"][0]["usage_status"] == "KNOWN"
    assert detail["tool_calls"][0]["tool_id"] == "evidence-catalog"
    assert detail["tool_calls"][0]["status"] == "SUCCEEDED"


def test_feedback_and_admin_api_are_authenticated_authorized_and_correlated():
    repository, telemetry, tracing = configured_lab()
    runs = AgentOrchestrator()
    run = runs.create_run("user-1", "Review evidence", "pet-a")
    result = AgentExecutionService(runs, FakeAIProvider(), lab=tracing).execute(
        "user-1", run.id, Media()
    )
    response_id = result["response_id"]

    original = {
        "repository": app.state.lab_repository,
        "telemetry": app.state.lab_telemetry,
        "tracing": app.state.lab_tracing,
        "feedback": app.state.lab_feedback,
        "queries": app.state.lab_queries,
        "operations": app.state.lab_operations,
        "feedback_enabled": app.state.settings.lab_feedback_enabled,
        "admin_enabled": app.state.settings.lab_admin_enabled,
    }
    app.state.lab_repository = repository
    app.state.lab_telemetry = telemetry
    app.state.lab_tracing = tracing
    app.state.lab_feedback = FeedbackService(
        repository, telemetry, hash_secret="test-secret"
    )
    app.state.lab_queries = LabQueryService(repository, minimum_sample=1)
    app.state.lab_operations = LabOperationsService(repository, hash_secret="test-secret", minimum_sample=1)
    app.state.settings.lab_feedback_enabled = True
    app.state.settings.lab_admin_enabled = True
    try:
        # Local auth creates user-1 as the first local user in the application
        # repository for this UID; bind the response to that canonical ID.
        principal_user = app.state.users.get_or_create("feedback-api-user")
        stored_response = repository.get_response(response_id)
        stored_response.owner_user_id = principal_user.id
        run_trace = repository.get_run(run.id)
        run_trace.owner_user_id = principal_user.id

        client = TestClient(app)
        auth = {"Authorization": "Bearer local-test:feedback-api-user"}
        submitted = client.put(
            f"/v1/agent-runs/{run.id}/responses/{response_id}/feedback",
            headers=auth,
            json={"value": "HELPED", "reasons": ["CLEAR"], "comment": "Útil"},
        )
        assert submitted.status_code == 200
        assert submitted.json()["value"] == "HELPED"
        assert client.get(
            f"/v1/agent-runs/{run.id}/responses/{response_id}/feedback", headers=auth
        ).status_code == 200

        forbidden = client.get("/v1/internal/lab/overview", headers=auth)
        assert forbidden.status_code == 403
        app.state.users.provision("feedback-api-user", UserRole.ADMIN)
        overview = client.get("/v1/internal/lab/overview", headers=auth)
        assert overview.status_code == 200
        assert overview.headers["cache-control"] == "private, max-age=15"
        assert overview.headers["etag"].startswith('W/"lab-')
        assert overview.json()["run_count"] == 1
        assert overview.json()["metrics"]["feedback_coverage"]["value"] == 1.0
        filtered_runs = client.get(
            "/v1/internal/lab/runs?status=SUCCEEDED"
            "&model_id=fake-platform-smoke-v1&feedback_value=HELPED"
            "&min_duration_ms=0&sort=STARTED_ASC",
            headers=auth,
        )
        assert filtered_runs.status_code == 200
        assert [item["run_id"] for item in filtered_runs.json()["items"]] == [run.id]
        assert client.get(f"/v1/internal/lab/runs/{run.id}", headers=auth).status_code == 200
        content = client.get(
            f"/v1/internal/lab/runs/{run.id}?include_content=true", headers=auth
        )
        assert content.status_code == 200
        assert content.headers["cache-control"] == "no-store"
        assert content.json()["content"]["available"] is False
        comments = client.get(
            "/v1/internal/lab/feedback?include_comment=true", headers=auth
        )
        assert comments.status_code == 200
        assert comments.headers["cache-control"] == "no-store"
        assert comments.json()["items"][0]["comment"] == "Útil"
        safety = client.post(
            f"/v1/agent-runs/{run.id}/responses/{response_id}/safety-report", headers=auth,
            json={"category": "FALSE_REASSURANCE", "severity": "HIGH", "description": "Needs review"},
        )
        assert safety.status_code == 201 and safety.json()["status"] == "OPEN"
        outcome = client.post(f"/v1/agent-runs/{run.id}/outcomes", headers=auth,
            json={"response_id": response_id, "outcome": "ESCALATED_TO_VET"})
        assert outcome.status_code == 201 and outcome.json()["outcome_value"] == "ESCALATED_TO_VET"
        audit = client.get("/v1/internal/lab/audit", headers=auth)
        assert audit.status_code == 200 and len(audit.json()["items"]) >= 2
    finally:
        app.state.lab_repository = original["repository"]
        app.state.lab_telemetry = original["telemetry"]
        app.state.lab_tracing = original["tracing"]
        app.state.lab_feedback = original["feedback"]
        app.state.lab_queries = original["queries"]
        app.state.lab_operations = original["operations"]
        app.state.settings.lab_feedback_enabled = original["feedback_enabled"]
        app.state.settings.lab_admin_enabled = original["admin_enabled"]


def test_demo_classification_never_appears_as_real():
    _, _, tracing = configured_lab()
    assert tracing.classification is DataClassification.TEST
