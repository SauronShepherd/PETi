from hashlib import sha256

from app.media.service import MediaService


class Blob:
    size = 3
    content_type = "image/jpeg"

    def download_as_bytes(self):
        return b"abc"


class Storage:
    def stat_object(self, bucket, name):
        return Blob()

    def checksum_object(self, blob):
        return sha256(blob.download_as_bytes()).hexdigest()


def test_finalize_uses_storage_checksum_adapter_for_blob_like_objects():
    pet = type("Pet", (), {"id": "pet-1"})()
    pets = type("Pets", (), {"get": lambda self, owner, pet_id: pet if owner == "u" and pet_id == pet.id else None})()
    service = MediaService(pets, storage=Storage())
    asset, session = service.create_session("u", pet.id, "IMAGE", "PROFILE", "image/jpeg", 3, "PROFILE_MEDIA", "k")
    asset.checksum_sha256_declared = sha256(b"abc").hexdigest()
    ready = service.finalize("u", asset.id, session.id)
    assert ready.checksum_sha256_verified == sha256(b"abc").hexdigest()
