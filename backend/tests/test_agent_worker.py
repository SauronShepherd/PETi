from app.main_worker import app
from fastapi.testclient import TestClient


def test_agent_worker_has_private_task_surface_only():
    paths = {route.path for route in app.routes}
    assert "/internal/tasks/agent" in paths
    assert "/v1/pets" not in paths


def test_agent_worker_rejects_missing_task_identity():
    response = TestClient(app).post("/internal/tasks/agent", json={})
    assert response.status_code == 401


def test_agent_worker_exposes_provider_backed_specialist_surface():
    paths = {route.path for route in app.routes}
    assert "/internal/tasks/specialist-gemini" in paths
