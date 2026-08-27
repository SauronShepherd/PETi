from app.media.firestore_metadata import FirestoreMediaMetadataStore
from app.media.firestore_repository import FirestoreMediaRepository


class Snapshot:
    id = "media-legacy"

    @staticmethod
    def to_dict():
        return {"owner_user_id": "owner"}


def test_media_firestore_adapters_restore_document_id_for_legacy_rows():
    assert FirestoreMediaMetadataStore._row(Snapshot())["id"] == "media-legacy"
    assert FirestoreMediaRepository._row(Snapshot())["id"] == "media-legacy"
