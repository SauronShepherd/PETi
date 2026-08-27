"""Firestore metadata persistence boundary for local emulator and production adapters."""

from typing import Any


def _where(query: Any, field: str, value: Any) -> Any:
    from google.cloud.firestore_v1.base_query import FieldFilter  # type: ignore[import-untyped]

    try:
        return query.where(filter=FieldFilter(field, "==", value))
    except TypeError:
        return query.where(field, "==", value)


class FirestoreMediaMetadataStore:
    def __init__(self, client: Any):
        self.client = client

    def save_asset(self, asset):
        self.client.collection("media_assets").document(asset.id).set(asset.__dict__)

    def save_session(self, session):
        self.client.collection("media_upload_sessions").document(session.id).set(session.__dict__)

    def atomic_state(self, asset, session=None):
        transaction = self.client.transaction()
        transaction._begin()
        asset_ref = self.client.collection("media_assets").document(asset.id)
        transaction.set(asset_ref, asset.__dict__)
        if session is not None:
            transaction.set(
                self.client.collection("media_upload_sessions").document(session.id),
                session.__dict__,
            )
        transaction.commit()

    def get_asset(self, media_id):
        snap = self.client.collection("media_assets").document(media_id).get()
        return self._row(snap) if snap.exists else None

    @staticmethod
    def _row(snapshot):
        row = dict(snapshot.to_dict() or {})
        row.setdefault("id", snapshot.id)
        return row

    def list_owned(self, user_id):
        return [
            self._row(x)
            for x in _where(self.client.collection("media_assets"), "owner_user_id", user_id).stream()
        ]

    def list_all_assets(self):
        return [self._row(x) for x in self.client.collection("media_assets").stream()]

    def list_all_sessions(self):
        return [self._row(x) for x in self.client.collection("media_upload_sessions").stream()]
