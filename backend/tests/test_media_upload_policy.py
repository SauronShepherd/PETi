from app.media.domain import MediaType, UploadStrategy
from app.media.upload_policy import StorageObjectNamer, UploadStrategyResolver


def test_upload_strategy_resolver_is_size_deterministic():
    resolver = UploadStrategyResolver()
    assert resolver.resolve(MediaType.IMAGE, 1) == UploadStrategy.SIMPLE_SIGNED_PUT
    assert resolver.resolve(MediaType.VIDEO, 5_000_000) == UploadStrategy.RESUMABLE


def test_storage_object_namer_is_opaque_and_contains_no_owner_or_pet_data():
    name = StorageObjectNamer().name("asset-123")
    assert name == "media/asset-123/source"
    assert "user" not in name.lower() and "pet" not in name.lower()
