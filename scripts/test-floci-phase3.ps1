$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
docker compose -f infra/local/docker-compose.yml up -d
$env:PETI_ENVIRONMENT = 'LOCAL'
$env:PETI_AUTH_MODE = 'LOCAL_TEST'
$env:PETI_STORAGE_MODE = 'FIRESTORE_EMULATOR'
$env:PETI_FIRESTORE_EMULATOR_HOST = '127.0.0.1:4588'
@'
import sys
sys.path.insert(0, "backend")
from fastapi.testclient import TestClient
from app.main import app
def h(uid): return {"Authorization": f"Bearer local-test:{uid}"}
with TestClient(app) as c:
    import uuid
    run_key = uuid.uuid4().hex
    a=h("phase3-floci-" + run_key)
    q=c.post("/v1/funding/quote",headers=a,json={"operation_type":"AI_PHOTO_STANDARD"})
    assert q.status_code==200 and q.json()["currently_fundable"]
    reservation=c.post("/v1/funding/reservations",headers={**a,"Idempotency-Key":f"floci-reservation-1-{run_key}"},json={"operation_type":"AI_PHOTO_STANDARD","operation_request_id":f"floci-op-1-{run_key}"})
    assert reservation.status_code==201
    reservation_id=reservation.json()["id"]
    consumed=c.post(f"/v1/funding/reservations/{reservation_id}/consume",headers={**a,"Execution-Id":"floci-exec-1"})
    assert consumed.status_code==200
    release=c.post("/v1/funding/reservations",headers={**a,"Idempotency-Key":f"floci-reservation-2-{run_key}"},json={"operation_type":"AI_PHOTO_STANDARD","operation_request_id":f"floci-op-2-{run_key}"})
    assert release.status_code==201
    released=c.post(f"/v1/funding/reservations/{release.json()['id']}/release",headers=a)
    assert released.status_code==200
    s=c.post("/v1/media/upload-sessions",headers={**a,"Idempotency-Key":f"floci-media-1-{run_key}"},json={"media_type":"IMAGE","purpose":"PROFILE","mime_type":"image/png","size_bytes":3,"retention_class":"PROFILE_MEDIA"})
    assert s.status_code==201 and s.json()["strategy"]=="SIMPLE_SIGNED_PUT"
    p=s.json(); media=p["media_asset"]; asset=app.state.media.assets[media["id"]]
    app.state.media.storage.put(asset.storage_bucket, asset.storage_object, b"abc", "image/png")
    finalized=c.post(f"/v1/media/{media['id']}/finalize",headers={**a,"Upload-Session-Id":p["upload_session_id"]})
    assert finalized.status_code==200 and finalized.json()["status"]=="READY"
    access=c.post(f"/v1/media/{media['id']}/access",headers=a)
    assert access.status_code==200 and access.json().get("read_url")
    assert c.delete(f"/v1/media/{media['id']}",headers=a).status_code==200
    from google.cloud import firestore
    db=firestore.Client(project="peti-local")
    assert list(db.collection("credit_grants").stream())
    assert list(db.collection("credit_reservations").stream())
    assert list(db.collection("credit_ledger").stream())
    assert db.collection("media_assets").document(media["id"]).get().exists
    from app.credits.service import CreditService
    from app.media.service import MediaService
    restarted_credits=CreditService(app.state.economic_store)
    assert restarted_credits.grants
    restarted_media=MediaService(app.state.pets, storage=app.state.media.storage, bucket="peti-local-media", metadata_store=app.state.media_metadata_store)
    assert restarted_media.assets[media["id"]].status.value=="DELETED"
    assert db.collection("media_upload_sessions").document(p["upload_session_id"]).get().exists
    from concurrent.futures import ThreadPoolExecutor
    def reserve_once(i):
        return c.post("/v1/funding/reservations",headers={**a,"Idempotency-Key":f"floci-concurrent-{run_key}-{i}"},json={"operation_type":"AI_VIDEO_STANDARD","operation_request_id":f"floci-concurrent-op-{run_key}-{i}"}).status_code
    with ThreadPoolExecutor(max_workers=4) as pool:
        statuses=list(pool.map(reserve_once, range(4)))
    assert statuses.count(201) <= 3 and all(x in (201,402,409) for x in statuses)
print("Floci Phase 3 metadata smoke passed")
'@ | python -
