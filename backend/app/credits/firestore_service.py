"""Small Firestore-backed economic journal used by LOCAL/FIRESTORE_EMULATOR."""

from threading import RLock
from typing import Any


def _where(query: Any, field: str, value: Any) -> Any:
    from google.cloud.firestore_v1.base_query import FieldFilter  # type: ignore[import-untyped]

    try:
        return query.where(filter=FieldFilter(field, "==", value))
    except TypeError:
        return query.where(field, "==", value)


class FirestoreEconomicStore:
    def __init__(self, client: Any):
        self.client = client
        self.lock = RLock()

    def append(self, collection: str, key: str, data: dict):
        self.client.collection(collection).document(key).set(data)

    def get(self, collection: str, key: str):
        snap = self.client.collection(collection).document(key).get()
        return snap.to_dict() if snap.exists else None

    def list_user(self, collection: str, user_id: str):
        return [
            x.to_dict()
            for x in _where(self.client.collection(collection), "user_id", user_id).stream()
        ]

    def list_all(self, collection: str):
        return [x.to_dict() for x in self.client.collection(collection).stream()]

    def transaction(self):
        return self.client.transaction()

    def atomic_commit(self, writes):
        transaction = self.client.transaction()
        for collection, key, data in writes:
            transaction.set(self.client.collection(collection).document(key), data)
        transaction.commit()

    def transactional_reservation(
        self,
        user_id,
        operation_request_id,
        idempotency_key,
        required,
        profile_version,
        operation_type,
        expires_at,
    ):
        with self.lock:
            return self._transactional_reservation(
                user_id,
                operation_request_id,
                idempotency_key,
                required,
                profile_version,
                operation_type,
                expires_at,
            )

    def _transactional_reservation(
        self,
        user_id,
        operation_request_id,
        idempotency_key,
        required,
        profile_version,
        operation_type,
        expires_at,
    ):
        from datetime import UTC, datetime
        from uuid import uuid4

        if isinstance(required, bool) or not isinstance(required, int) or required <= 0:
            raise ValueError("FUNDING_REQUIRED")
        transaction = self.client.transaction()
        transaction._begin()
        grants = list(_where(self.client.collection("credit_grants"), "user_id", user_id).stream(transaction=transaction))
        existing = list(_where(_where(self.client.collection("credit_reservations"), "user_id", user_id), "idempotency_key", idempotency_key).stream(transaction=transaction))
        if existing:
            return existing[0].to_dict()
        available = []
        for snap in grants:
            data = snap.to_dict()
            remaining = data.get("remaining_amount", 0)
            reserved = data.get("reserved_amount", 0)
            if (
                isinstance(remaining, bool)
                or not isinstance(remaining, int)
                or remaining < 0
                or isinstance(reserved, bool)
                or not isinstance(reserved, int)
                or reserved < 0
            ):
                continue
            free = remaining - reserved
            if free > 0:
                available.append((snap, data, free))
        available.sort(
            key=lambda item: (
                item[1].get("expires_at") or datetime.max.replace(tzinfo=UTC),
                item[1].get("created_at") or datetime.min.replace(tzinfo=UTC),
                item[0].id,
            )
        )
        left = required
        allocation = []
        for snap, data, free in available:
            amount = min(left, free)
            data["reserved_amount"] = data.get("reserved_amount", 0) + amount
            transaction.set(snap.reference, data)
            allocation.append(
                {"grant_id": snap.id, "amount": amount, "funding_source": data["source"]}
            )
            left -= amount
            if not left:
                break
        if left:
            raise ValueError("FUNDING_REQUIRED")
        reservation_id = str(uuid4())
        reservation = {
            "id": reservation_id,
            "user_id": user_id,
            "operation_type": operation_type,
            "cost_profile_version": profile_version,
            "requested_amount": required,
            "status": "RESERVED",
            "allocation": allocation,
            "operation_request_id": operation_request_id,
            "idempotency_key": idempotency_key,
            "created_at": datetime.now(UTC),
            "expires_at": expires_at,
        }
        transaction.create(
            self.client.collection("credit_reservations").document(reservation_id), reservation
        )
        for item in allocation:
            entry = {
                "id": str(uuid4()),
                "user_id": user_id,
                "direction": "RESERVE",
                "amount": item["amount"],
                "grant_id": item["grant_id"],
                "reservation_id": reservation_id,
                "operation_request_id": operation_request_id,
                "source": item["funding_source"],
                "idempotency_key": idempotency_key,
                "created_at": datetime.now(UTC),
            }
            transaction.create(self.client.collection("credit_ledger").document(entry["id"]), entry)
        transaction.commit()
        return reservation

    def transactional_transition(self, reservation_id, user_id, mode, request_key):
        if mode not in {"consume", "release"}:
            raise ValueError("CREDIT_TRANSITION_INVALID")
        transaction = self.client.transaction()
        transaction._begin()
        ref = self.client.collection("credit_reservations").document(reservation_id)
        snap = ref.get(transaction=transaction)
        if not snap.exists or snap.to_dict().get("user_id") != user_id:
            raise ValueError("CREDIT_RESERVATION_NOT_FOUND")
        reservation = snap.to_dict()
        status = reservation.get("status")
        target = "CONSUMED" if mode == "consume" else "RELEASED"
        if status == target:
            return reservation
        if status != "RESERVED":
            raise ValueError(
                "CREDIT_RESERVATION_NOT_CONSUMABLE"
                if mode == "consume"
                else "CREDIT_RESERVATION_NOT_RELEASABLE"
            )
        allocations = reservation.get("allocation")
        if not isinstance(allocations, list):
            raise ValueError("LEDGER_INVARIANT_VIOLATION")  # noqa: TRY004
        for allocation in allocations:
            if (
                not isinstance(allocation, dict)
                or not isinstance(allocation.get("grant_id"), str)
                or not isinstance(allocation.get("funding_source"), str)
            ):
                raise ValueError("LEDGER_INVARIANT_VIOLATION")  # noqa: TRY004
            grant_ref = self.client.collection("credit_grants").document(allocation["grant_id"])
            grant_snap = grant_ref.get(transaction=transaction)
            if not grant_snap.exists:
                raise ValueError("LEDGER_INVARIANT_VIOLATION")
            grant = grant_snap.to_dict()
            amount = allocation["amount"]
            remaining = grant.get("remaining_amount", 0)
            reserved = grant.get("reserved_amount", 0)
            if (
                isinstance(remaining, bool)
                or not isinstance(remaining, int)
                or remaining < 0
                or isinstance(reserved, bool)
                or not isinstance(reserved, int)
                or reserved < 0
                or isinstance(amount, bool)
                or not isinstance(amount, int)
                or amount <= 0
                or amount > reserved
                or (mode == "consume" and amount > remaining)
            ):
                raise ValueError("LEDGER_INVARIANT_VIOLATION")
            if mode == "consume":
                grant["remaining_amount"] = remaining - amount
            grant["reserved_amount"] = reserved - amount
            # The store serializes local emulator transitions. Snapshot writes
            # are deliberately used here because replaying a transform such as
            # Increment during a Firestore transaction retry would apply the
            # debit more than once.
            transaction.set(grant_ref, grant)
            entry = {
                "id": str(__import__("uuid").uuid4()),
                "user_id": user_id,
                "direction": "CONSUME" if mode == "consume" else "RELEASE",
                "amount": amount,
                "grant_id": allocation["grant_id"],
                "reservation_id": reservation_id,
                "source": allocation["funding_source"],
                "idempotency_key": request_key,
                "created_at": __import__("datetime").datetime.now(__import__("datetime").UTC),
            }
            transaction.create(self.client.collection("credit_ledger").document(entry["id"]), entry)
        reservation["status"] = target
        reservation["consumed_at" if mode == "consume" else "released_at"] = __import__(
            "datetime"
        ).datetime.now(__import__("datetime").UTC)
        transaction.set(ref, reservation)
        transaction.commit()
        return reservation
