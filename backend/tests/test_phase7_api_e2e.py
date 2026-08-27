from uuid import uuid4

from app.main import app
from app.records.vault import CandidateFact, CandidateStatus
from fastapi.testclient import TestClient


def auth(user: str):
    return {"Authorization": f"Bearer local-test:{user}"}


def test_http_measurement_rejects_ai_estimated_source_class():
    user = "phase6-api-" + uuid4().hex
    headers = auth(user)
    client = TestClient(app)
    pet = client.post(
        "/v1/pets", headers={**headers, "Idempotency-Key": "pet-" + user},
        json={"species": "DOG", "display_name": "Measurement pet"},
    ).json()
    response = client.post(
        f"/v1/pets/{pet['id']}/measurements", headers={**headers, "Idempotency-Key": "measurement-" + user},
        json={
            "measurement_type": "WEIGHT", "original_value": "10", "original_unit": "kg",
            "source_class": "AI_ESTIMATED",
        },
    )
    assert response.status_code == 400
    assert response.json()["code"] == "MEASUREMENT_AI_SOURCE_NOT_CLIENT_CREATABLE"


def test_record_vault_local_api_flow_to_documented_measurement_and_delete():
    user = "phase7-api-" + uuid4().hex
    headers = auth(user)
    client = TestClient(app)
    pet = client.post(
        "/v1/pets",
        headers={**headers, "Idempotency-Key": "pet-" + user},
        json={"species": "DOG", "display_name": "Record Vault pet"},
    ).json()
    media = client.post(
        "/v1/media/upload-sessions",
        headers={**headers, "Idempotency-Key": "media-" + user},
        json={
            "animal_id": pet["id"], "media_type": "DOCUMENT", "purpose": "DOCUMENT_SOURCE",
            "mime_type": "application/pdf", "size_bytes": 128, "retention_class": "CLINICAL_DOCUMENT",
        },
    ).json()
    media_id = media["media_asset"]["id"]
    asset = app.state.media.assets[media_id]
    app.state.media.storage.put(asset.storage_bucket, asset.storage_object, b"x" * 128, "application/pdf")
    assert client.post(
        f"/v1/media/{media_id}/finalize", headers={**headers, "Upload-Session-Id": media["upload_session_id"]}
    ).status_code == 200
    record = client.post(
        f"/v1/pets/{pet['id']}/records", headers=headers,
        json={"source_media_id": media_id, "document_type": "VETERINARY_REPORT", "title": "Visit"},
    )
    assert record.status_code == 201
    record_id = record.json()["id"]
    owner_id = record.json()["owner_user_id"]
    source_access = client.post(f"/v1/records/{record_id}/access", headers=headers)
    assert source_access.status_code == 200
    read_url = source_access.json().get("read_url", "")
    if str(app.state.settings.storage_mode) == "FIRESTORE_EMULATOR":
        assert "127.0.0.1:4588" in read_url
    else:
        assert read_url.startswith("fake://read/")
    assert "storage_object" not in source_access.json()
    other = auth("phase7-other-" + uuid4().hex)
    assert client.get(f"/v1/pets/{pet['id']}/records", headers=other).json() == []
    assert client.get(f"/v1/records/{record_id}", headers=other).status_code == 404
    assert client.post(f"/v1/records/{record_id}/access", headers=other).status_code == 404
    assert client.post(
        f"/v1/records/{record_id}/extract", headers=other,
        json={"fixture_text": "Weight: 44.1 lb", "analysis_id": "cross-owner"},
    ).status_code == 404
    assert client.post(f"/v1/records/{record_id}/extract", headers=headers, json={
        "document_metadata_candidates": [], "fact_candidates": [], "extraction_limitations": [],
    }).status_code == 503
    assert record_id in app.state.records.documents
    assert app.state.records.documents[record_id].owner_user_id == owner_id
    assert app.state.settings.environment.value == "LOCAL"

    worker_payload = {"owner_user_id": owner_id, "record_id": record_id, "analysis_id": "phase7-api-analysis",
                      "extraction": {"document_metadata_candidates": [], "extraction_limitations": [], "fact_candidates": [{
                          "fact_type": "WEIGHT", "candidate_value": "44.1", "candidate_unit": "lb",
                          "source_anchor": {"document_id": record_id, "anchor_type": "PAGE", "page_number": 1},
                          "confidence": "HIGH"}]}}
    unauthorized_worker = client.post(
        "/v1/internal/tasks/record-extraction",
        headers={"X-Task-Service-Identity": "untrusted", "X-Task-Audience": "local"},
        json=worker_payload,
    )
    assert unauthorized_worker.status_code == 401
    extraction = client.post(
        "/v1/internal/tasks/record-extraction",
        headers={"X-Task-Service-Identity": "floci-cloud-tasks", "X-Task-Audience": "local"},
        json=worker_payload,
    )
    assert extraction.status_code == 200 and extraction.json()["status"] == "review_required", extraction.text
    candidate = client.get(f"/v1/records/{record_id}/candidate-facts", headers=headers).json()[0]
    assert candidate["status"] == "PENDING_REVIEW"
    assert client.get(f"/v1/records/{record_id}/candidate-facts", headers=other).status_code == 404
    assert client.post(f"/v1/candidate-facts/{candidate['id']}/confirm", headers=other).status_code == 404
    confirmed = client.post(f"/v1/candidate-facts/{candidate['id']}/confirm", headers=headers)
    assert confirmed.status_code == 200
    fact = confirmed.json()["documented_fact"]
    assert fact["source_class"] == "DOCUMENTED" and fact["value"] == "44.1" and fact["unit"] == "lb"
    pending_id = "pending-timeline-" + uuid4().hex
    rejected_id = "rejected-timeline-" + uuid4().hex
    app.state.records.candidates[pending_id] = CandidateFact(
        id=pending_id, document_id=record_id, owner_user_id=user, animal_id=pet["id"],
        extraction_analysis_id="timeline-analysis", fact_type="WEIGHT", candidate_value="1",
    )
    app.state.records.candidates[rejected_id] = CandidateFact(
        id=rejected_id, document_id=record_id, owner_user_id=user, animal_id=pet["id"],
        extraction_analysis_id="timeline-analysis", fact_type="WEIGHT", candidate_value="2",
        status=CandidateStatus.REJECTED,
    )
    timeline = client.get(f"/v1/pets/{pet['id']}/timeline", headers=headers)
    assert timeline.status_code == 200
    timeline_ids = {item["source_entity_id"] for item in timeline.json()}
    assert fact["id"] in timeline_ids
    assert pending_id not in timeline_ids and rejected_id not in timeline_ids
    assert client.get(f"/v1/pets/{pet['id']}/documented-facts", headers=other).json() == []
    assert client.get(f"/v1/documented-facts/{fact['id']}", headers=other).status_code == 404
    assert client.delete(f"/v1/records/{record_id}?confirm_dependencies=true", headers=other).status_code == 404
    measurements = client.get(f"/v1/pets/{pet['id']}/measurements", headers=headers).json()
    assert any(item["source_class"] == "DOCUMENTED" and item["original_value"] == "44.1" for item in measurements)

    preview = client.get(f"/v1/records/{record_id}/deletion-preview", headers=headers).json()
    assert preview["dependent_documented_fact_count"] == 1
    assert client.delete(f"/v1/records/{record_id}", headers=headers).status_code == 409
    assert client.delete(f"/v1/records/{record_id}?confirm_dependencies=true", headers=headers).status_code == 200
    assert client.get(f"/v1/records/{record_id}", headers=headers).status_code == 404
    assert client.get(f"/v1/pets/{pet['id']}/documented-facts", headers=headers).json() == []
