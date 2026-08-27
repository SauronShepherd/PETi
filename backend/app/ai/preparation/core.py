from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlsplit


class PreparedMediaKind(StrEnum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"


@dataclass(frozen=True)
class PreparedMedia:
    asset_id: str
    kind: PreparedMediaKind
    reference: str
    mime_type: str | None = None


@dataclass(frozen=True)
class PreparedMediaPackage:
    items: tuple[PreparedMedia, ...]
    version: str = "1.0.0"


class MediaPreparationError(ValueError):
    pass


class _ModalityPreparer:
    kind: PreparedMediaKind

    def prepare_one(self, asset: dict) -> PreparedMedia:
        if not isinstance(asset, dict) or not isinstance(asset.get("id"), str) or not asset["id"].strip():
            raise MediaPreparationError("MEDIA_ID_REQUIRED")
        reference = asset.get("reference")
        mime_type = asset.get("mime_type")
        if not isinstance(reference, str) or not reference.strip():
            raise MediaPreparationError("MEDIA_SOURCE_REQUIRED")
        parsed = urlsplit(reference)
        if parsed.scheme != "gs" or not parsed.netloc or not parsed.path.strip("/"):
            raise MediaPreparationError("MEDIA_SOURCE_NOT_PROVIDER_READABLE")
        if not isinstance(mime_type, str) or not mime_type.strip() or "/" not in mime_type:
            raise MediaPreparationError("MEDIA_MIME_REQUIRED")
        return PreparedMedia(
            asset["id"], self.kind, reference, mime_type,
        )


class ImageMediaPreparer(_ModalityPreparer):
    kind = PreparedMediaKind.IMAGE


class VideoMediaPreparer(_ModalityPreparer):
    kind = PreparedMediaKind.VIDEO


class AudioMediaPreparer(_ModalityPreparer):
    kind = PreparedMediaKind.AUDIO


class DocumentMediaPreparer(_ModalityPreparer):
    kind = PreparedMediaKind.DOCUMENT


class MediaPreparer:
    """Dispatch to a versioned, modality-specific preparation boundary."""

    def __init__(self):
        self._preparers = {
            PreparedMediaKind.IMAGE: ImageMediaPreparer(),
            PreparedMediaKind.VIDEO: VideoMediaPreparer(),
            PreparedMediaKind.AUDIO: AudioMediaPreparer(),
            PreparedMediaKind.DOCUMENT: DocumentMediaPreparer(),
        }

    def prepare(self, assets: list[dict]) -> PreparedMediaPackage:
        if not assets:
            raise MediaPreparationError("MEDIA_REQUIRED")
        items = []
        for asset in assets:
            try:
                kind = PreparedMediaKind(str(asset.get("kind", "IMAGE")).upper())
            except ValueError as exc:
                raise MediaPreparationError("MEDIA_TYPE_UNSUPPORTED") from exc
            items.append(self._preparers[kind].prepare_one(asset))
        return PreparedMediaPackage(tuple(items))
