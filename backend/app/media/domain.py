from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class MediaType(StrEnum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"


class MediaPurpose(StrEnum):
    PROFILE = "PROFILE"
    ANALYSIS_SOURCE = "ANALYSIS_SOURCE"
    DOCUMENT_SOURCE = "DOCUMENT_SOURCE"
    TEMPORARY_CAPTURE = "TEMPORARY_CAPTURE"
    INTERNAL_FIXTURE = "INTERNAL_FIXTURE"


class RetentionClass(StrEnum):
    TRANSIENT_ANALYSIS = "TRANSIENT_ANALYSIS"
    RETAINED_ANALYSIS_MEDIA = "RETAINED_ANALYSIS_MEDIA"
    PROFILE_MEDIA = "PROFILE_MEDIA"
    CLINICAL_DOCUMENT = "CLINICAL_DOCUMENT"
    INTERNAL_FIXTURE = "INTERNAL_FIXTURE"


class MediaStatus(StrEnum):
    PENDING_UPLOAD = "PENDING_UPLOAD"
    UPLOADING = "UPLOADING"
    UPLOADED_UNVERIFIED = "UPLOADED_UNVERIFIED"
    READY = "READY"
    FAILED = "FAILED"
    DELETE_PENDING = "DELETE_PENDING"
    DELETED = "DELETED"
    EXPIRED = "EXPIRED"


LEGAL_MEDIA_TRANSITIONS: dict[MediaStatus, set[MediaStatus]] = {
    MediaStatus.PENDING_UPLOAD: {MediaStatus.UPLOADING, MediaStatus.DELETE_PENDING, MediaStatus.EXPIRED},
    # An upload abandoned beyond retention is terminally expired even when
    # it was interrupted after the client entered the UPLOADING state.
    MediaStatus.UPLOADING: {MediaStatus.UPLOADED_UNVERIFIED, MediaStatus.FAILED, MediaStatus.DELETE_PENDING, MediaStatus.EXPIRED},
    MediaStatus.UPLOADED_UNVERIFIED: {MediaStatus.READY, MediaStatus.FAILED, MediaStatus.DELETE_PENDING},
    MediaStatus.READY: {MediaStatus.DELETE_PENDING, MediaStatus.EXPIRED},
    MediaStatus.FAILED: {MediaStatus.UPLOADING, MediaStatus.DELETE_PENDING, MediaStatus.EXPIRED},
    MediaStatus.DELETE_PENDING: {MediaStatus.DELETED, MediaStatus.FAILED},
    MediaStatus.DELETED: set(),
    MediaStatus.EXPIRED: set(),
}


class UploadStrategy(StrEnum):
    SIMPLE_SIGNED_PUT = "SIMPLE_SIGNED_PUT"
    RESUMABLE = "RESUMABLE"
    INTERNAL_FIXTURE = "INTERNAL_FIXTURE"


class UploadSessionStatus(StrEnum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CANCELED = "CANCELED"


@dataclass
class MediaAsset:
    id: str
    owner_user_id: str
    media_type: MediaType
    purpose: MediaPurpose
    mime_type_declared: str
    retention_class: RetentionClass
    animal_id: str | None = None
    original_filename: str | None = None
    size_bytes_declared: int | None = None
    size_bytes_verified: int | None = None
    checksum_sha256_declared: str | None = None
    checksum_sha256_verified: str | None = None
    storage_generation: str | None = None
    storage_bucket: str = "local-media"
    storage_object: str = ""
    upload_strategy: UploadStrategy = UploadStrategy.SIMPLE_SIGNED_PUT
    status: MediaStatus = MediaStatus.PENDING_UPLOAD
    delete_after: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    uploaded_at: datetime | None = None
    finalized_at: datetime | None = None
    deleted_at: datetime | None = None

    def transition(self, target: MediaStatus) -> None:
        target = MediaStatus(target)
        if target not in LEGAL_MEDIA_TRANSITIONS[self.status]:
            raise ValueError(f"MEDIA_ILLEGAL_TRANSITION:{self.status}->{target}")
        self.status = target


@dataclass
class MediaUploadSession:
    id: str
    media_asset_id: str
    user_id: str
    strategy: UploadStrategy
    expected_content_type: str
    expected_size_max: int
    authorization_expires_at: datetime
    status: UploadSessionStatus = UploadSessionStatus.CREATED
    idempotency_key: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finalized_at: datetime | None = None
