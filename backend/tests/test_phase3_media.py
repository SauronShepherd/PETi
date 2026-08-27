from hashlib import sha256

import pytest
from app.media.domain import (
    MediaAsset,
    MediaPurpose,
    MediaStatus,
    MediaType,
    RetentionClass,
    UploadStrategy,
)
from app.media.service import MediaError, MediaService
from app.media.storage import FakeObjectStorage


class Pets:
    def get(self, user_id, pet_id):
        return {"u1": {"pet-1": object()}}.get(user_id, {}).get(pet_id)


def service():
    return MediaService(Pets(), FakeObjectStorage())


def test_private_upload_finalize_access_and_delete():
    s = service()
    a, session = s.create_session(
        "u1",
        "pet-1",
        MediaType.IMAGE,
        MediaPurpose.ANALYSIS_SOURCE,
        "image/jpeg",
        3,
        RetentionClass.TRANSIENT_ANALYSIS,
        "k",
    )
    assert a.storage_object.startswith("media/") and "pet-1" not in a.storage_object
    s.storage.put(a.storage_bucket, a.storage_object, b"abc", "image/jpeg")
    ready = s.finalize("u1", a.id, session.id)
    assert (
        ready.status == MediaStatus.READY
        and ready.checksum_sha256_verified == sha256(b"abc").hexdigest()
    )
    assert s.access("u1", a.id)["read_url"].startswith("fake://")
    assert s.delete("u1", a.id).status == MediaStatus.DELETED
    assert s.get_owned("u1", a.id) is None


def test_idempotency_ownership_and_large_strategy():
    s = service()
    first = s.create_session(
        "u1",
        None,
        MediaType.VIDEO,
        MediaPurpose.TEMPORARY_CAPTURE,
        "video/mp4",
        5_000_000,
        RetentionClass.TRANSIENT_ANALYSIS,
        "same",
    )
    assert (
        s.create_session(
            "u1",
            None,
            MediaType.VIDEO,
            MediaPurpose.TEMPORARY_CAPTURE,
            "video/mp4",
            5_000_000,
            RetentionClass.TRANSIENT_ANALYSIS,
            "same",
        )[0].id
        == first[0].id
    )
    assert first[0].upload_strategy == UploadStrategy.RESUMABLE
    with pytest.raises(MediaError, match="PET_NOT_FOUND"):
        s.create_session(
            "u2",
            "pet-1",
            MediaType.IMAGE,
            MediaPurpose.PROFILE,
            "image/png",
            1,
            RetentionClass.PROFILE_MEDIA,
            "other",
        )


def test_finalize_rejects_wrong_metadata_and_cross_user():
    s = service()
    a, session = s.create_session(
        "u1",
        None,
        MediaType.IMAGE,
        MediaPurpose.PROFILE,
        "image/png",
        3,
        RetentionClass.PROFILE_MEDIA,
        "x",
    )
    s.storage.put(a.storage_bucket, a.storage_object, b"abc", "image/jpeg")
    with pytest.raises(MediaError, match="MEDIA_NOT_FOUND"):
        s.finalize("u2", a.id, session.id)
    with pytest.raises(MediaError, match="MEDIA_CONTENT_TYPE_MISMATCH"):
        s.finalize("u1", a.id, session.id)


def test_media_state_machine_rejects_illegal_transitions():
    asset = MediaAsset(
        "m1", "u1", MediaType.IMAGE, MediaPurpose.PROFILE, "image/png",
        RetentionClass.PROFILE_MEDIA,
    )
    with pytest.raises(ValueError, match="MEDIA_ILLEGAL_TRANSITION"):
        asset.transition(MediaStatus.READY)
    asset.transition(MediaStatus.UPLOADING)
    asset.transition(MediaStatus.UPLOADED_UNVERIFIED)
    asset.transition(MediaStatus.READY)
    with pytest.raises(ValueError, match="MEDIA_ILLEGAL_TRANSITION"):
        asset.transition(MediaStatus.PENDING_UPLOAD)


def test_finalize_uses_upload_state_machine():
    s = service()
    asset, session = s.create_session(
        "u1", None, MediaType.IMAGE, MediaPurpose.PROFILE, "image/png", 3,
        RetentionClass.PROFILE_MEDIA, "state-machine",
    )
    s.storage.put(asset.storage_bucket, asset.storage_object, b"abc", "image/png")
    assert s.finalize("u1", asset.id, session.id).status == MediaStatus.READY


def test_cross_user_media_access_and_delete_are_denied():
    s = service()
    asset, session = s.create_session(
        "u1", None, MediaType.IMAGE, MediaPurpose.PROFILE, "image/png", 3,
        RetentionClass.PROFILE_MEDIA, "cross-user",
    )
    s.storage.put(asset.storage_bucket, asset.storage_object, b"abc", "image/png")
    s.finalize("u1", asset.id, session.id)
    with pytest.raises(MediaError, match="MEDIA_ACCESS_UNAVAILABLE"):
        s.access("u2", asset.id)
    with pytest.raises(MediaError, match="MEDIA_NOT_FOUND"):
        s.delete("u2", asset.id)
    assert s.access("u1", asset.id)["read_url"].startswith("fake://")


def test_webp_is_explicitly_rejected_until_all_paths_are_validated():
    s = service()
    with pytest.raises(MediaError, match="MEDIA_MIME_UNSUPPORTED"):
        s.create_session(
            "u1", None, MediaType.IMAGE, MediaPurpose.PROFILE, "image/webp", 3,
            RetentionClass.PROFILE_MEDIA, "webp-disabled",
        )
