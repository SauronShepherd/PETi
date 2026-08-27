from dataclasses import dataclass
from enum import StrEnum


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
        if not asset.get("id"):
            raise MediaPreparationError("MEDIA_ID_REQUIRED")
        return PreparedMedia(
            str(asset["id"]), self.kind,
            str(asset.get("reference", asset["id"])), asset.get("mime_type"),
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
