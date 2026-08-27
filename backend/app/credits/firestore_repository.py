"""Firestore persistence boundary for economic data.

All writes are append/create or transaction callbacks; no ledger update operation is exposed.
"""

from typing import Any

from .domain import CreditGrant, CreditLedgerEntry, CreditReservation


def _where(query: Any, field: str, value: Any) -> Any:
    from google.cloud.firestore_v1.base_query import FieldFilter  # type: ignore[import-untyped]

    try:
        return query.where(filter=FieldFilter(field, "==", value))
    except TypeError:
        return query.where(field, "==", value)


class FirestoreCreditRepository:
    def __init__(self, client: Any):
        self.client = client

    def create_grant(self, grant: CreditGrant):
        self.client.collection("credit_grants").document(grant.id).create(grant.__dict__)
        return grant

    def append_entry(self, entry: CreditLedgerEntry):
        self.client.collection("credit_ledger").document(entry.id).create(entry.__dict__)
        return entry

    def create_reservation(self, reservation: CreditReservation):
        self.client.collection("credit_reservations").document(reservation.id).create(
            reservation.__dict__
        )
        return reservation

    def list_user_entries(self, user_id: str):
        return [
            x.to_dict()
            for x in _where(self.client.collection("credit_ledger"), "user_id", user_id).stream()
        ]

    def find_by_idempotency(self, user_id: str, idempotency_key: str):
        items = _where(_where(self.client.collection("credit_ledger"), "user_id", user_id), "idempotency_key", idempotency_key).stream()
        return next(iter(items), None)
