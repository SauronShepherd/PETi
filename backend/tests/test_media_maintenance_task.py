from app.main import app
from fastapi.testclient import TestClient


def test_media_maintenance_task_requires_task_identity():
    response = TestClient(app).post("/v1/internal/tasks/media-maintenance")

    assert response.status_code == 401
    assert response.json()["code"] == "TASK_SERVICE_IDENTITY_INVALID"


def test_media_maintenance_task_runs_retention_and_abandoned_sweep(monkeypatch):
    calls = []

    monkeypatch.setattr(
        app.state.retention,
        "expire_due",
        lambda now: calls.append("due") or 2,
    )
    monkeypatch.setattr(
        app.state.retention,
        "expire_abandoned_uploads",
        lambda now: calls.append("abandoned") or 3,
    )

    response = TestClient(app).post(
        "/v1/internal/tasks/media-maintenance",
        headers={"X-Task-Service-Identity": "floci-cloud-tasks"},
    )

    assert response.status_code == 200
    assert response.json() == {"expired_media": 2, "abandoned_uploads": 3}
    assert calls == ["due", "abandoned"]


def test_media_maintenance_business_value_error_is_not_mapped_to_auth_failure(monkeypatch):
    monkeypatch.setattr(
        app.state.retention,
        "expire_due",
        lambda now: (_ for _ in ()).throw(ValueError("RETENTION_STORE_FAILURE")),
    )

    response = TestClient(app, raise_server_exceptions=False).post(
        "/v1/internal/tasks/media-maintenance",
        headers={"X-Task-Service-Identity": "floci-cloud-tasks"},
    )

    assert response.status_code == 500


def test_media_maintenance_task_uses_dedicated_authenticator_non_local(monkeypatch):
    from app.config.settings import Environment

    calls = []

    class DedicatedAuthenticator:
        def verify_bearer(self, authorization):
            calls.append(authorization)

    monkeypatch.setattr(app.state.settings, "environment", Environment.DEV)
    monkeypatch.setattr(app.state, "maintenance_task_authenticator", DedicatedAuthenticator())
    monkeypatch.setattr(app.state.retention, "expire_due", lambda now: 0)
    monkeypatch.setattr(app.state.retention, "expire_abandoned_uploads", lambda now: 0)

    response = TestClient(app).post(
        "/v1/internal/tasks/media-maintenance",
        headers={"Authorization": "Bearer scheduler-token"},
    )

    assert response.status_code == 200
    assert calls == ["Bearer scheduler-token"]
