from app.main import app
from fastapi.testclient import TestClient


def h(uid="a"):
    return {"Authorization": f"Bearer local-test:{uid}"}


def test_auth_me_and_user_isolation():
    c = TestClient(app)
    missing = c.get("/v1/me")
    assert missing.status_code == 401 and missing.json()["code"] == "AUTH_MISSING_TOKEN"
    a = c.get("/v1/me", headers=h("phase1-a"))
    assert a.status_code == 200 and a.json()["role"] == "CUSTOMER"
    b = c.get("/v1/me", headers=h("phase1-b"))
    assert b.json()["id"] != a.json()["id"]
    p = c.post(
        "/v1/pets",
        headers={**h("phase1-a"), "Idempotency-Key": "k1"},
        json={"display_name": "Milo", "species": "DOG"},
    )
    assert p.status_code == 201
    pet = p.json()
    assert c.get("/v1/pets", headers=h("phase1-b")).json() == []
    assert c.get("/v1/pets/" + pet["id"], headers=h("phase1-b")).status_code == 404


def test_species_and_idempotency_crud():
    c = TestClient(app)
    assert c.get("/v1/species").json()[0]["species_code"] == "DOG"
    headers = {**h("phase1-c"), "Idempotency-Key": "same-key"}
    first = c.post("/v1/pets", headers=headers, json={"display_name": "Nala", "species": "DOG"})
    assert first.json()["profile_complete"] is False
    assert "health_score" not in first.json()
    assert "weight" not in first.json()
    assert "activity" not in first.json()
    retry = c.post("/v1/pets", headers=headers, json={"display_name": "Nala", "species": "DOG"})
    assert retry.json()["id"] == first.json()["id"]
    assert (
        c.post(
            "/v1/pets", headers=headers, json={"display_name": "Other", "species": "DOG"}
        ).status_code
        == 409
    )
    pet = first.json()
    assert (
        c.patch(
            "/v1/pets/" + pet["id"], headers=h("phase1-c"), json={"display_name": "Nala 2"}
        ).status_code
        == 200
    )
    assert c.delete("/v1/pets/" + pet["id"], headers=h("phase1-c")).status_code == 204
    assert c.get("/v1/pets/" + pet["id"], headers=h("phase1-c")).status_code == 404


def test_unknown_species_is_not_defaulted():
    c = TestClient(app)
    assert (
        c.post(
            "/v1/pets",
            headers={**h("phase1-d"), "Idempotency-Key": "bad"},
            json={"display_name": "x", "species": "CAT"},
        ).status_code
        == 400
    )
