from app.auth.task_auth import TaskAuthenticator
from app.main import app as api_app
from app.main_worker import app
from fastapi.testclient import TestClient


def test_worker_surface_does_not_mount_customer_routes():
    paths = {route.path for route in app.routes}
    assert "/internal/tasks/analysis" in paths
    assert "/v1/pets" not in paths
    assert "/v1/pets/{pet_id}/checks" not in paths


def test_worker_exposes_private_health_contract():
    paths = {route.path for route in app.routes}
    assert "/health/live" in paths
    assert "/health/ready" in paths


def test_worker_rejects_customer_firebase_bearer_token(monkeypatch):
    def customer_token_verifier(token, audience):
        assert token == "firebase-customer-token"
        return {"sub": "firebase-customer-uid", "aud": audience}

    monkeypatch.setattr(
        api_app.state,
        "task_authenticator",
        TaskAuthenticator(
            expected_service_account="peti-worker@project.iam.gserviceaccount.com",
            expected_audience="https://worker.example/internal/tasks/analysis",
            local=False,
            token_verifier=customer_token_verifier,
        ),
    )

    response = TestClient(app).post(
        "/internal/tasks/analysis",
        headers={"Authorization": "Bearer firebase-customer-token"},
        json={"job_id": "job-never-reached"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "TASK_SERVICE_IDENTITY_INVALID"
