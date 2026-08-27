from uuid import uuid4

from .domain import MediaType, UploadStrategy


class UploadStrategyResolver:
    def __init__(self, resumable_threshold: int = 5_000_000):
        self.resumable_threshold = resumable_threshold

    def resolve(self, media_type: MediaType, size: int | None) -> UploadStrategy:
        del media_type  # strategy is size-based today; type remains part of the contract
        return (
            UploadStrategy.RESUMABLE
            if (size or 0) >= self.resumable_threshold
            else UploadStrategy.SIMPLE_SIGNED_PUT
        )


class StorageObjectNamer:
    prefix = "media"

    def name(self, asset_id: str | None = None) -> str:
        opaque_id = asset_id or str(uuid4())
        return f"{self.prefix}/{opaque_id}/source"
