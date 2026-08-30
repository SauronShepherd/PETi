from app.main import app
from fastapi.testclient import TestClient


def test_web_origin_is_allowed_for_browser_authenticated_requests() -> None:
    response = TestClient(app).options(
        "/v1/pets",
        headers={
            "Origin": "http://localhost:4173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:4173"
    assert response.headers["access-control-allow-credentials"] == "true"
