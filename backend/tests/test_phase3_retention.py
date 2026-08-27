from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier

from app.media.domain import MediaPurpose, MediaStatus, MediaType, RetentionClass
from app.media.retention import RetentionService
from app.media.service import MediaService
from app.media.storage import FakeObjectStorage


def test_retention_policy_and_expiry_delete_private_object():
    service = MediaService(object(), FakeObjectStorage())
    retention = RetentionService(service)
    asset, _ = service.create_session(
        "u",
        None,
        MediaType.IMAGE,
        MediaPurpose.PROFILE,
        "image/png",
        3,
        RetentionClass.TRANSIENT_ANALYSIS,
        "r1",
    )
    service.storage.put(asset.storage_bucket, asset.storage_object, b"abc", "image/png")
    service.finalize("u", asset.id, next(iter(service.sessions)))
    retention.apply_policy(asset)
    asset.delete_after = datetime.now(UTC) - timedelta(seconds=1)
    assert retention.expire_due() == 1 and asset.status == MediaStatus.EXPIRED


def test_abandoned_upload_cleanup_expires_only_stale_unfinalized_assets():
    service = MediaService(object(), FakeObjectStorage())
    retention = RetentionService(service)
    abandoned, abandoned_session = service.create_session(
        "u", None, MediaType.IMAGE, MediaPurpose.PROFILE, "image/png", 3,
        RetentionClass.TRANSIENT_ANALYSIS, "abandoned",
    )
    fresh, _ = service.create_session(
        "u", None, MediaType.IMAGE, MediaPurpose.PROFILE, "image/png", 3,
        RetentionClass.TRANSIENT_ANALYSIS, "fresh",
    )
    service.storage.put(abandoned.storage_bucket, abandoned.storage_object, b"old", "image/png")
    abandoned.created_at = datetime.now(UTC) - timedelta(days=2)
    assert retention.expire_abandoned_uploads(ttl=timedelta(days=1)) == 1
    assert abandoned.status == MediaStatus.EXPIRED
    assert abandoned_session.status.value == "EXPIRED"
    assert service.storage.stat_object(abandoned.storage_bucket, abandoned.storage_object) is None
    assert fresh.status == MediaStatus.PENDING_UPLOAD


def test_abandoned_upload_cleanup_uses_legal_transition_from_uploading():
    service = MediaService(object(), FakeObjectStorage())
    retention = RetentionService(service)
    asset, _ = service.create_session(
        "u", None, MediaType.IMAGE, MediaPurpose.PROFILE, "image/png", 3,
        RetentionClass.TRANSIENT_ANALYSIS, "uploading-abandoned",
    )
    asset.transition(MediaStatus.UPLOADING)
    asset.created_at = datetime.now(UTC) - timedelta(days=2)
    assert retention.expire_abandoned_uploads(ttl=timedelta(days=1)) == 1
    assert asset.status == MediaStatus.EXPIRED


def test_retention_policy_uses_injected_clock():
    service = MediaService(object(), FakeObjectStorage())
    now = datetime(2026, 1, 10, tzinfo=UTC)
    retention = RetentionService(service, clock=lambda: now)
    asset, _ = service.create_session(
        "u", None, MediaType.IMAGE, MediaPurpose.PROFILE, "image/png", 3,
        RetentionClass.TRANSIENT_ANALYSIS, "clocked",
    )
    retention.apply_policy(asset)
    assert asset.delete_after == now + timedelta(days=7)


def test_change_class_persists_retention_policy():
    class Metadata:
        def __init__(self):
            self.saved = []

        def save_asset(self, asset):
            self.saved.append((asset.retention_class, asset.delete_after))

        def save_session(self, session):
            return None

    metadata = Metadata()
    service = MediaService(object(), FakeObjectStorage(), metadata_store=metadata)
    retention = RetentionService(service, clock=lambda: datetime(2026, 1, 10, tzinfo=UTC))
    asset, _ = service.create_session(
        "u", None, MediaType.IMAGE, MediaPurpose.PROFILE, "image/png", 3,
        RetentionClass.TRANSIENT_ANALYSIS, "persisted-class",
    )
    retention.change_class("u", asset.id, "CLINICAL_DOCUMENT")
    assert metadata.saved[-1] == (RetentionClass.CLINICAL_DOCUMENT, datetime(2027, 1, 10, tzinfo=UTC))


def test_expire_due_persists_terminal_asset_state():
    class Metadata:
        def __init__(self):
            self.saved = []

        def save_asset(self, asset):
            self.saved.append(asset)

        def save_session(self, session):
            return None

    metadata = Metadata()
    service = MediaService(object(), FakeObjectStorage(), metadata_store=metadata)
    retention = RetentionService(service, clock=lambda: datetime(2026, 1, 10, tzinfo=UTC))
    asset, _ = service.create_session(
        "u", None, MediaType.IMAGE, MediaPurpose.PROFILE, "image/png", 3,
        RetentionClass.TRANSIENT_ANALYSIS, "expire-persisted",
    )
    session_id = next(iter(service.sessions))
    service.storage.put(asset.storage_bucket, asset.storage_object, b"abc", "image/png")
    service.finalize("u", asset.id, session_id)
    asset.delete_after = datetime(2026, 1, 9, tzinfo=UTC)
    assert retention.expire_due() == 1
    assert metadata.saved[-1].status == MediaStatus.EXPIRED


def test_concurrent_expiry_sweeps_delete_one_asset():
    service = MediaService(object(), FakeObjectStorage())
    retention = RetentionService(service, clock=lambda: datetime(2026, 1, 10, tzinfo=UTC))
    asset, session = service.create_session(
        "u", None, MediaType.IMAGE, MediaPurpose.PROFILE, "image/png", 3,
        RetentionClass.TRANSIENT_ANALYSIS, "concurrent-expiry",
    )
    service.storage.put(asset.storage_bucket, asset.storage_object, b"abc", "image/png")
    service.finalize("u", asset.id, session.id)
    asset.delete_after = datetime(2026, 1, 9, tzinfo=UTC)
    barrier = Barrier(2)

    def expire():
        barrier.wait()
        return retention.expire_due()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: expire(), range(2)))

    assert sum(results) == 1
    assert asset.status == MediaStatus.EXPIRED
