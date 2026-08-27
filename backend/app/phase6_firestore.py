"""Firestore persistence adapter for Phase 6 canonical records."""

from dataclasses import asdict
from typing import Any


def _where(query: Any, field: str, value: Any) -> Any:
    from google.cloud.firestore_v1.base_query import FieldFilter  # type: ignore[import-untyped]

    try:
        return query.where(filter=FieldFilter(field, "==", value))
    except TypeError:
        return query.where(field, "==", value)


class FirestorePhase6Store:
    def __init__(self, client: Any):
        self.client = client

    def put(self, collection: str, record: Any) -> None:
        self.client.collection(collection).document(record.id).set(asdict(record))

    def put_user(self, collection: str, user_id: str, record: Any) -> None:
        data = asdict(record)
        data["user_id"] = user_id
        document_id = getattr(record, "id", None) or user_id
        self.client.collection(collection).document(document_id).set(data)

    def put_raw(self, collection: str, document_id: str, data: dict[str, Any]) -> None:
        self.client.collection(collection).document(document_id).set(data)

    def delete(self, collection: str, record_id: str) -> None:
        self.client.collection(collection).document(record_id).delete()

    @staticmethod
    def _row(snapshot: Any) -> dict[str, Any]:
        row = dict(snapshot.to_dict() or {})
        # Firestore document IDs are not included in document fields.  Every
        # durable domain hydrator needs the canonical ID to reconstruct its
        # entity and to delete the exact row during privacy erasure.
        row.setdefault("id", snapshot.id)
        return row

    def list_owned(self, collection: str, owner_user_id: str) -> list[dict[str, Any]]:
        return [self._row(snapshot) for snapshot in _where(self.client.collection(collection), "owner_user_id", owner_user_id).stream()]

    def list_user(self, collection: str, user_id: str) -> list[dict[str, Any]]:
        return [self._row(snapshot) for snapshot in _where(self.client.collection(collection), "user_id", user_id).stream()]

    def all(self, collection: str) -> list[dict[str, Any]]:
        return [self._row(snapshot) for snapshot in self.client.collection(collection).stream()]
