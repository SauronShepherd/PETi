from datetime import UTC, datetime, timedelta
from uuid import uuid4

from .domain import (
    MediaAsset,
    MediaPurpose,
    MediaStatus,
    MediaType,
    MediaUploadSession,
    RetentionClass,
    UploadSessionStatus,
    UploadStrategy,
)
from .storage import FakeObjectStorage, object_checksum
from .upload_policy import StorageObjectNamer, UploadStrategyResolver

MIME = {
    # WEBP remains intentionally disabled until viewer and extraction paths are
    # validated together; accepting it here would create a half-wired path.
    MediaType.IMAGE: {"image/jpeg", "image/png"},
    MediaType.VIDEO: {"video/mp4", "video/quicktime"},
    MediaType.AUDIO: {"audio/mp4", "audio/mpeg", "audio/wav"},
    MediaType.DOCUMENT: {"application/pdf", "image/jpeg", "image/png"},
}


class MediaError(ValueError):
    pass


class MediaService:
    def __init__(self, pets, storage=None, bucket="local-media", metadata_store=None, clock=None):
        self.pets = pets
        self.metadata_store = metadata_store
        self.clock = clock or (lambda: datetime.now(UTC))
        self.storage = storage or FakeObjectStorage(bucket)
        self.bucket = bucket
        self.assets = {}
        self.sessions = {}
        self.idempotency = {}
        self.strategy_resolver = UploadStrategyResolver()
        self.object_namer = StorageObjectNamer()
        self._hydrate()

    def _hydrate(self):
        if not self.metadata_store or not hasattr(self.metadata_store, "list_all_assets"):
            return
        try:
            assets = self.metadata_store.list_all_assets()
        except Exception:  # noqa: BLE001 - transient metadata outage must not crash startup
            assets = []
        for raw in assets:
            try:
                data = dict(raw)
                for key in ("delete_after", "created_at", "uploaded_at", "finalized_at", "deleted_at"):
                    value = data.get(key)
                    if value is not None and not isinstance(value, datetime):
                        data[key] = datetime.fromisoformat(str(value))
                for key, enum_type in (
                    ("media_type", MediaType),
                    ("purpose", MediaPurpose),
                    ("retention_class", RetentionClass),
                    ("status", MediaStatus),
                    ("upload_strategy", UploadStrategy),
                ):
                    data[key] = enum_type(data[key])
                self.assets[data["id"]] = MediaAsset(
                    **{k: data[k] for k in MediaAsset.__dataclass_fields__ if k in data}
                )
            except (KeyError, TypeError, ValueError):
                continue
        try:
            sessions = self.metadata_store.list_all_sessions()
        except Exception:  # noqa: BLE001 - transient metadata outage must not crash startup
            sessions = []
        for raw in sessions:
            try:
                data = dict(raw)
                for key in ("authorization_expires_at", "created_at", "finalized_at"):
                    value = data.get(key)
                    if value is not None and not isinstance(value, datetime):
                        data[key] = datetime.fromisoformat(str(value))
                data["strategy"] = UploadStrategy(data["strategy"])
                data["status"] = UploadSessionStatus(data["status"])
                self.sessions[data["id"]] = MediaUploadSession(
                    **{k: data[k] for k in MediaUploadSession.__dataclass_fields__ if k in data}
                )
                session = self.sessions[data["id"]]
                if session.idempotency_key:
                    asset = self.assets.get(session.media_asset_id)
                    if asset:
                        self.idempotency[(session.user_id, session.idempotency_key)] = (asset, session)
            except (KeyError, TypeError, ValueError):
                continue

    def _strategy(self, media_type, size):
        return self.strategy_resolver.resolve(media_type, size)

    def create_session(
        self, user_id, animal_id, media_type, purpose, mime_type, size, retention, idem
    ):
        idem_key = (user_id, idem)
        if idem_key in self.idempotency:
            return self.idempotency[idem_key]
        mt = MediaType(media_type)
        pu = MediaPurpose(purpose)
        rc = RetentionClass(retention)
        if mime_type not in MIME[mt]:
            raise MediaError("MEDIA_MIME_UNSUPPORTED")
        if size is not None and size < 0:
            raise MediaError("MEDIA_TOO_LARGE")
        if animal_id and not self.pets.get(user_id, animal_id):
            raise MediaError("PET_NOT_FOUND")
        aid, sid = str(uuid4()), str(uuid4())
        strategy = self._strategy(mt, size)
        obj = self.object_namer.name(aid)
        asset = MediaAsset(
            aid,
            user_id,
            mt,
            pu,
            mime_type,
            rc,
            animal_id=animal_id,
            size_bytes_declared=size,
            storage_bucket=self.bucket,
            storage_object=obj,
            upload_strategy=strategy,
        )
        session = MediaUploadSession(
            sid,
            aid,
            user_id,
            strategy,
            mime_type,
            size or 50_000_000,
            self.clock() + timedelta(minutes=15),
            idempotency_key=idem,
        )
        self.assets[aid] = asset
        self.sessions[sid] = session
        self.idempotency[idem_key] = (asset, session)
        if self.metadata_store:
            self.metadata_store.save_asset(asset)
            self.metadata_store.save_session(session)
        return asset, session

    def finalize(self, user_id, media_id, session_id):
        a = self.assets.get(media_id)
        s = self.sessions.get(session_id)
        if (
            not a
            or a.owner_user_id != user_id
            or not s
            or s.media_asset_id != media_id
            or s.user_id != user_id
        ):
            raise MediaError("MEDIA_NOT_FOUND")
        if a.status == MediaStatus.READY:
            return a
        if a.status not in {MediaStatus.PENDING_UPLOAD, MediaStatus.FAILED}:
            raise MediaError("MEDIA_NOT_FINALIZABLE")
        a.transition(MediaStatus.UPLOADING)
        obj = self.storage.stat_object(a.storage_bucket, a.storage_object)
        if not obj:
            raise MediaError("MEDIA_OBJECT_NOT_FOUND")
        if obj.content_type != a.mime_type_declared:
            raise MediaError("MEDIA_CONTENT_TYPE_MISMATCH")
        actual_size = len(obj.content) if hasattr(obj, "content") else obj.size
        if actual_size > s.expected_size_max or (
            a.size_bytes_declared is not None and actual_size != a.size_bytes_declared
        ):
            raise MediaError("MEDIA_OBJECT_MISMATCH")
        if hasattr(self.storage, "checksum_object"):
            checksum = self.storage.checksum_object(obj)
        else:
            checksum = object_checksum(obj) if hasattr(obj, "content") else None
        if a.checksum_sha256_declared and a.checksum_sha256_declared != checksum:
            raise MediaError("MEDIA_CHECKSUM_MISMATCH")
        a.size_bytes_verified = actual_size
        a.checksum_sha256_verified = checksum
        generation = getattr(obj, "generation", None)
        if generation is not None:
            a.storage_generation = str(generation)
        a.transition(MediaStatus.UPLOADED_UNVERIFIED)
        a.transition(MediaStatus.READY)
        a.finalized_at = self.clock()
        a.uploaded_at = a.finalized_at
        s.status = UploadSessionStatus.COMPLETED
        s.finalized_at = a.finalized_at
        if self.metadata_store:
            if hasattr(self.metadata_store, "atomic_state"):
                self.metadata_store.atomic_state(a, s)
            else:
                self.metadata_store.save_asset(a)
                self.metadata_store.save_session(s)
        return a

    def get_owned(self, user_id, media_id):
        a = self.assets.get(media_id)
        return (
            a
            if a
            and a.owner_user_id == user_id
            and a.status not in {MediaStatus.DELETED, MediaStatus.EXPIRED}
            else None
        )

    def resolve_ai_media(self, owner_user_id, media_asset_ids, animal_id=None):
        """Resolve owned, finalized media into provider-safe storage descriptors.

        Callers may submit identifiers only.  An identifier is never treated as
        a URI, a filename, or inline media content; the provider media-part
        source is constructed solely from validated server-side storage
        coordinates. The returned ``id`` is a MediaAsset/provenance ID, not
        multimedia content.
        """
        if not media_asset_ids:
            raise MediaError("MEDIA_REQUIRED")
        descriptors = []
        seen = set()
        now = self.clock()
        for media_asset_id in media_asset_ids:
            if (
                not isinstance(media_asset_id, str)
                or not media_asset_id.strip()
                or media_asset_id in seen
                or "://" in media_asset_id
                or media_asset_id.startswith("/")
            ):
                raise MediaError("MEDIA_AI_SOURCE_INVALID")
            seen.add(media_asset_id)
            asset = self.assets.get(media_asset_id)
            # A long-lived worker may have started before the API finalized
            # this asset. Refresh the single requested identity from the
            # durable metadata store instead of relying on process memory.
            if asset is None and self.metadata_store and hasattr(self.metadata_store, "get_asset"):
                raw = self.metadata_store.get_asset(media_asset_id)
                if raw:
                    data = dict(raw)
                    for key in ("delete_after", "created_at", "uploaded_at", "finalized_at", "deleted_at"):
                        value = data.get(key)
                        if value is not None and not isinstance(value, datetime):
                            data[key] = datetime.fromisoformat(str(value))
                    for key, enum_type in (
                        ("media_type", MediaType), ("purpose", MediaPurpose),
                        ("retention_class", RetentionClass), ("status", MediaStatus),
                        ("upload_strategy", UploadStrategy),
                    ):
                        data[key] = enum_type(data[key])
                    asset = MediaAsset(**{k: data[k] for k in MediaAsset.__dataclass_fields__ if k in data})
                    self.assets[media_asset_id] = asset
            if not asset:
                raise MediaError("MEDIA_AI_SOURCE_NOT_FOUND")
            if asset.owner_user_id != owner_user_id:
                raise MediaError("MEDIA_AI_SOURCE_NOT_OWNED")
            if asset.status != MediaStatus.READY:
                raise MediaError("MEDIA_AI_SOURCE_NOT_READY")
            if asset.deleted_at is not None or (asset.delete_after is not None and asset.delete_after <= now):
                raise MediaError("MEDIA_AI_SOURCE_UNAVAILABLE")
            if animal_id is not None and asset.animal_id != animal_id:
                raise MediaError("MEDIA_AI_SOURCE_ANIMAL_MISMATCH")
            if asset.media_type not in MIME:
                raise MediaError("MEDIA_AI_SOURCE_MODALITY_UNSUPPORTED")
            if asset.mime_type_declared not in MIME[asset.media_type]:
                raise MediaError("MEDIA_AI_SOURCE_MIME_INVALID")
            bucket = asset.storage_bucket.strip() if isinstance(asset.storage_bucket, str) else ""
            storage_object = asset.storage_object.strip() if isinstance(asset.storage_object, str) else ""
            if not bucket or not storage_object or "://" in storage_object or storage_object.startswith("/"):
                raise MediaError("MEDIA_AI_SOURCE_STORAGE_INVALID")
            stored = self.storage.stat_object(bucket, storage_object)
            if not stored:
                raise MediaError("MEDIA_AI_SOURCE_OBJECT_MISSING")
            if stored.content_type != asset.mime_type_declared:
                raise MediaError("MEDIA_AI_SOURCE_MIME_MISMATCH")
            stored_generation = getattr(stored, "generation", None)
            if asset.storage_generation is not None and str(stored_generation) != asset.storage_generation:
                raise MediaError("MEDIA_AI_SOURCE_GENERATION_MISMATCH")
            if (asset.checksum_sha256_verified is not None and hasattr(self.storage, "checksum_object")
                    and self.storage.checksum_object(stored) != asset.checksum_sha256_verified):
                raise MediaError("MEDIA_AI_SOURCE_CHECKSUM_MISMATCH")
            descriptors.append({
                "id": asset.id,
                "asset_id": asset.id,
                "kind": asset.media_type.value,
                "mime_type": asset.mime_type_declared,
                "reference": f"gs://{bucket}/{storage_object}",
            })
        return descriptors

    def list_owned(self, user_id):
        return [
            a
            for a in self.assets.values()
            if a.owner_user_id == user_id
            and a.status not in {MediaStatus.DELETED, MediaStatus.EXPIRED}
        ]

    def access(self, user_id, media_id):
        a = self.get_owned(user_id, media_id)
        if not a or a.status != MediaStatus.READY:
            raise MediaError("MEDIA_ACCESS_UNAVAILABLE")
        return self.storage.create_read_authorization(a.storage_bucket, a.storage_object)

    def delete(self, user_id, media_id):
        a = self.get_owned(user_id, media_id)
        if not a:
            raise MediaError("MEDIA_NOT_FOUND")
        self.storage.delete_object(a.storage_bucket, a.storage_object)
        a.transition(MediaStatus.DELETE_PENDING)
        a.transition(MediaStatus.DELETED)
        if self.metadata_store:
            if hasattr(self.metadata_store, "atomic_state"):
                self.metadata_store.atomic_state(a)
            else:
                self.metadata_store.save_asset(a)
        a.deleted_at = self.clock()
        return a
