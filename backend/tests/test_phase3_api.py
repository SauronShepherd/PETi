from app.main import app
from fastapi.testclient import TestClient


def auth(uid):
    return {"Authorization": f"Bearer local-test:{uid}"}


def test_media_api_requires_auth_and_is_owner_scoped():
    client = TestClient(app)
    assert client.get("/v1/media").status_code == 401
    bad = client.post(
        "/v1/media/upload-sessions",
        headers={**auth("a"), "Idempotency-Key": "m1"},
        json={
            "animal_id": "unknown",
            "media_type": "IMAGE",
            "purpose": "PROFILE",
            "mime_type": "image/png",
            "size_bytes": 3,
            "retention_class": "PROFILE_MEDIA",
        },
    )
    assert bad.status_code == 400
    created = client.post(
        "/v1/media/upload-sessions",
        headers={**auth("a"), "Idempotency-Key": "m2"},
        json={
            "media_type": "IMAGE",
            "purpose": "PROFILE",
            "mime_type": "image/png",
            "size_bytes": 3,
            "retention_class": "PROFILE_MEDIA",
        },
    )
    assert created.status_code == 201
    payload = created.json()
    asset = payload["media_asset"]
    media_id = asset["id"]
    retry = client.post(
        "/v1/media/upload-sessions",
        headers={**auth("a"), "Idempotency-Key": "m2"},
        json={
            "media_type": "IMAGE",
            "purpose": "PROFILE",
            "mime_type": "image/png",
            "size_bytes": 3,
            "retention_class": "PROFILE_MEDIA",
        },
    )
    assert retry.json()["media_asset"]["id"] == media_id
    assert client.get(f"/v1/media/{media_id}", headers=auth("b")).status_code == 404
    assert client.delete(f"/v1/media/{media_id}", headers=auth("b")).status_code == 404


def test_media_api_retention_and_refresh_are_owner_scoped():
    client = TestClient(app)
    headers = {**auth("retention-user"), "Idempotency-Key": "r1"}
    response = client.post(
        "/v1/media/upload-sessions",
        headers=headers,
        json={
            "media_type": "DOCUMENT",
            "purpose": "DOCUMENT_SOURCE",
            "mime_type": "application/pdf",
            "size_bytes": 3,
            "retention_class": "TRANSIENT_ANALYSIS",
        },
    )
    media_id = response.json()["media_asset"]["id"]
    assert (
        client.post(
            f"/v1/media/{media_id}/upload-authorization", headers=auth("retention-user")
        ).status_code
        == 200
    )
    changed = client.patch(
        f"/v1/media/{media_id}/retention",
        headers=auth("retention-user"),
        json={"retention_class": "CLINICAL_DOCUMENT"},
    )
    assert changed.status_code == 200 and changed.json()["retention_class"] == "CLINICAL_DOCUMENT"
    invalid = client.patch(
        f"/v1/media/{media_id}/retention",
        headers=auth("retention-user"),
        json={"retention_class": "NOT_A_RETENTION_CLASS"},
    )
    assert invalid.status_code == 400


def test_media_api_does_not_refresh_authorization_after_finalize():
    client = TestClient(app)
    response = client.post(
        "/v1/media/upload-sessions",
        headers={**auth("finalized-user"), "Idempotency-Key": "finalized-1"},
        json={
            "media_type": "IMAGE",
            "purpose": "ANALYSIS_SOURCE",
            "mime_type": "image/jpeg",
            "size_bytes": 3,
            "retention_class": "TRANSIENT_ANALYSIS",
        },
    )
    media_id = response.json()["media_asset"]["id"]
    app.state.media.assets[media_id].status = "READY"
    blocked = client.post(
        f"/v1/media/{media_id}/upload-authorization",
        headers=auth("finalized-user"),
    )
    assert blocked.status_code == 409
    assert "MEDIA_UPLOAD_ALREADY_FINALIZED" in blocked.text
