from datetime import UTC, datetime, timedelta
from threading import RLock

from .domain import MediaStatus, RetentionClass, UploadSessionStatus
from .service import MediaError

DEFAULT_RETENTION = {
    RetentionClass.TRANSIENT_ANALYSIS: timedelta(days=7),
    RetentionClass.RETAINED_ANALYSIS_MEDIA: timedelta(days=30),
    RetentionClass.PROFILE_MEDIA: None,
    RetentionClass.CLINICAL_DOCUMENT: timedelta(days=365),
    RetentionClass.INTERNAL_FIXTURE: timedelta(days=1),
}


class RetentionService:
    def __init__(self, media_service, clock=None):
        self.media = media_service
        self.clock = clock or (lambda: datetime.now(UTC))
        self._lock = RLock()

    def apply_policy(self, asset):
        duration = DEFAULT_RETENTION[asset.retention_class]
        asset.delete_after = self.clock() + duration if duration else None
        return asset

    def expire_due(self, now=None):
        with self._lock:
            return self._expire_due(now)

    def _expire_due(self, now=None):
        now = now or self.clock()
        count = 0
        for asset in list(self.media.assets.values()):
            if (
                asset.status == MediaStatus.READY
                and asset.delete_after
                and asset.delete_after <= now
            ):
                self.media.storage.delete_object(asset.storage_bucket, asset.storage_object)
                asset.transition(MediaStatus.EXPIRED)
                asset.deleted_at = now
                if self.media.metadata_store:
                    self.media.metadata_store.save_asset(asset)
                count += 1
        return count

    def expire_abandoned_uploads(self, now=None, ttl=timedelta(hours=24)):
        """Expire upload sessions that never reached authoritative finalization."""
        with self._lock:
            return self._expire_abandoned_uploads(now, ttl)

    def _expire_abandoned_uploads(self, now=None, ttl=timedelta(hours=24)):
        now = now or self.clock()
        cutoff = now - ttl
        count = 0
        for asset in list(self.media.assets.values()):
            if asset.status not in {MediaStatus.PENDING_UPLOAD, MediaStatus.UPLOADING}:
                continue
            if asset.created_at > cutoff:
                continue
            self.media.storage.delete_object(asset.storage_bucket, asset.storage_object)
            asset.transition(MediaStatus.EXPIRED)
            asset.deleted_at = now
            session = next(
                (item for item in self.media.sessions.values() if item.media_asset_id == asset.id),
                None,
            )
            if session:
                session.status = UploadSessionStatus.EXPIRED
                session.finalized_at = now
            if self.media.metadata_store:
                self.media.metadata_store.save_asset(asset)
                if session:
                    self.media.metadata_store.save_session(session)
            count += 1
        return count

    def change_class(self, user_id, media_id, retention_class):
        asset = self.media.get_owned(user_id, media_id)
        if not asset:
            raise MediaError("MEDIA_NOT_FOUND")
        asset.retention_class = RetentionClass(retention_class)
        asset = self.apply_policy(asset)
        if self.media.metadata_store:
            self.media.metadata_store.save_asset(asset)
        return asset
