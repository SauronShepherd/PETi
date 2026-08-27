from datetime import UTC, datetime, timedelta

from app.credits.domain import FundingSource
from app.credits.service import CreditService
from app.future.service import FutureService
from app.media.service import MediaService


class Store:
    def __init__(self):
        self.data = {
            "credit_grants": [],
            "credit_reservations": [],
            "media_assets": [],
            "media_upload_sessions": [],
            "future_domain_items": [],
        }

    def list_all(self, collection):
        return list(self.data[collection])

    def append(self, collection, key, data):
        self.data.setdefault(collection, []).append(dict(data))

    def all(self, collection):
        return list(self.data.get(collection, []))

    def put_raw(self, collection, key, data):
        rows = self.data.setdefault(collection, [])
        rows[:] = [row for row in rows if row.get("id") != key]
        rows.append(dict(data))


def test_credit_service_hydrates_grants_after_restart():
    store = Store()
    first = CreditService(store)
    grant = first.grant("u", FundingSource.PROMOTIONAL, 4)
    restarted = CreditService(store)
    assert restarted.grants[grant.id].remaining_amount == 4


def test_media_service_hydration_contract_is_optional():
    service = MediaService(object(), metadata_store=Store())
    assert service.assets == {} and service.sessions == {}


def test_media_upload_session_uses_injected_clock():
    instant = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
    service = MediaService(object(), clock=lambda: instant)
    _, session = service.create_session(
        "u", None, "IMAGE", "PROFILE", "image/png", 3, "PROFILE_MEDIA", "clocked-session"
    )
    assert session.authorization_expires_at == instant + timedelta(minutes=15)


def test_media_service_hydrates_serialized_lifecycle_timestamps():
    instant = datetime.now(UTC)

    class Metadata:
        def list_all_assets(self):
            return [{
                "id": "asset-1", "owner_user_id": "u", "media_type": "IMAGE", "purpose": "PROFILE",
                "mime_type_declared": "image/jpeg", "retention_class": "PROFILE_MEDIA", "storage_object": "object-1",
                "status": "READY", "upload_strategy": "SIMPLE_SIGNED_PUT",
                "created_at": instant.isoformat(), "uploaded_at": instant.isoformat(), "deleted_at": None,
            }]

        def list_all_sessions(self):
            return [{
                "id": "session-1", "media_asset_id": "asset-1", "user_id": "u", "strategy": "SIMPLE_SIGNED_PUT",
                "expected_content_type": "image/jpeg", "expected_size_max": 1000,
                "status": "CREATED",
                "authorization_expires_at": instant.isoformat(), "created_at": instant.isoformat(), "finalized_at": None,
            }]

    service = MediaService(object(), metadata_store=Metadata())
    assert service.assets["asset-1"].created_at == instant
    assert service.sessions["session-1"].authorization_expires_at == instant


def test_credit_service_hydrates_serialized_lifecycle_timestamps():
    instant = datetime.now(UTC)

    class CreditStore:
        def list_all(self, collection):
            if collection == "credit_grants":
                return [{
                    "id": "grant-1", "user_id": "u", "source": "PROMOTIONAL",
                    "original_amount": 2, "remaining_amount": 2, "reserved_amount": 0,
                    "created_at": instant.isoformat(), "expires_at": instant.isoformat(),
                    "exhausted_at": None,
                }]
            if collection == "credit_reservations":
                return [{
                    "id": "reservation-1", "user_id": "u", "operation_type": "AI_PHOTO_STANDARD",
                    "cost_profile_version": 1, "requested_amount": 1, "status": "RELEASED",
                    "allocation": [], "operation_request_id": "op", "idempotency_key": "idem",
                    "created_at": instant.isoformat(), "expires_at": instant.isoformat(),
                    "released_at": instant.isoformat(), "consumed_at": None,
                }]
            return []

    service = CreditService(CreditStore())
    assert service.grants["grant-1"].expires_at == instant
    assert service.reservations["reservation-1"].released_at == instant


def test_future_domain_hydrates_persisted_items_after_restart():
    store = Store()

    class Pets:
        def get(self, owner, pet_id):
            return object()

    first = FutureService(Pets(), store=store)
    item = first.create("u", "ASSISTANT_THREAD", "pet-1", {"messages": []})
    restarted = FutureService(Pets(), store=store)
    assert restarted.owned("u", item.id, "ASSISTANT_THREAD").payload == {"messages": []}


def test_future_domain_hydrates_serialized_lifecycle_timestamps():
    store = Store()
    class Pets:
        def get(self, owner, pet_id):
            return object()

    service = FutureService(Pets(), store=store)
    item = service.create("u", "ASSISTANT_THREAD", "pet-1", {"messages": []})
    row = store.data["future_domain_items"][0]
    row["created_at"] = item.created_at.isoformat()
    row["updated_at"] = item.updated_at.isoformat()

    restarted = FutureService(Pets(), store=store)
    restored = restarted.owned("u", item.id, "ASSISTANT_THREAD")
    assert restored.created_at == item.created_at
    assert restored.updated_at == item.updated_at
