from typing import Any

from .domain import MediaAsset, MediaUploadSession


def _where(query: Any, field: str, value: Any) -> Any:
    from google.cloud.firestore_v1.base_query import FieldFilter  # type: ignore[import-untyped]

    try:
        return query.where(filter=FieldFilter(field, "==", value))
    except TypeError:
        return query.where(field, "==", value)


class FirestoreMediaRepository:
    def __init__(self, client: Any):
        self.client = client

    def create_pending(self, asset: MediaAsset):
        self.client.collection("media_assets").document(asset.id).create(asset.__dict__)
        return asset

    def create_session(self, session: MediaUploadSession):
        self.client.collection("media_upload_sessions").document(session.id).create(
            session.__dict__
        )
        return session

    def get_owned(self, user_id, media_id):
        snap = self.client.collection("media_assets").document(media_id).get()
        if not snap.exists:
            return None
        data = self._row(snap)
        return MediaAsset(**data) if data.get("owner_user_id") == user_id else None

    @staticmethod
    def _row(snapshot):
        row = dict(snapshot.to_dict() or {})
        row.setdefault("id", snapshot.id)
        return row

    def list_owned(self, user_id):
        return [
            MediaAsset(**self._row(x))
            for x in _where(self.client.collection("media_assets"), "owner_user_id", user_id).stream()
        ]

    def mark(self, asset):
        self.client.collection("media_assets").document(asset.id).set(asset.__dict__)
        return asset
