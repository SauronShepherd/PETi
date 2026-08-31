from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from enum import Enum
from threading import RLock
from uuid import uuid4

from .domain import (
    Allocation,
    CostProfile,
    CreditGrant,
    CreditLedgerEntry,
    CreditReservation,
    FundingSource,
    LedgerDirection,
    OperationType,
    ReservationStatus,
)

DEFAULT_COSTS = {
    OperationType.PETI_CHECK: 1,
    OperationType.AI_PHOTO_STANDARD: 1,
    OperationType.AI_AUDIO_STANDARD: 2,
    OperationType.AI_VIDEO_STANDARD: 3,
    OperationType.AI_DOCUMENT_EXTRACTION: 1,
    OperationType.AI_SPECIALIST_STANDARD: 2,
    OperationType.MEDIA_RETENTION_UNIT: 1,
}


class FundingError(ValueError):
    pass


class CreditService:
    def __init__(self, persistence=None, clock=None):
        self.persistence = persistence
        self.clock = clock or (lambda: datetime.now(UTC))
        self.lock = RLock()
        self.profiles = {op: CostProfile(op, 1, cost) for op, cost in DEFAULT_COSTS.items()}
        self.grants = {}
        self.reservations = {}
        self.ledger = []
        self.idempotency = {}
        self._hydrate()

    def _hydrate(self):
        if not self.persistence or not hasattr(self.persistence, "list_all"):
            return
        from .domain import Allocation

        try:
            grants = self.persistence.list_all("credit_grants")
        except Exception:  # noqa: BLE001 - transient journal outage must not crash startup
            grants = []
        for data in grants:
            try:
                data = dict(data)
                for key in ("created_at", "expires_at", "exhausted_at"):
                    value = data.get(key)
                    if value is not None and not isinstance(value, datetime):
                        data[key] = datetime.fromisoformat(str(value))
                data["source"] = FundingSource(data["source"])
                self.grants[data["id"]] = CreditGrant(
                    **{k: data[k] for k in CreditGrant.__dataclass_fields__ if k in data}
                )
                grant = self.grants[data["id"]]
                if grant.source == FundingSource.FREE_ALLOWANCE and grant.source_reference == "allowance:v1":
                    self.idempotency[(grant.user_id, "FREE_ALLOWANCE")] = grant
            except (KeyError, TypeError, ValueError):
                continue
        try:
            reservations = self.persistence.list_all("credit_reservations")
        except Exception:  # noqa: BLE001 - transient journal outage must not crash startup
            reservations = []
        for data in reservations:
            try:
                data = dict(data)
                for key in ("created_at", "expires_at", "consumed_at", "released_at"):
                    value = data.get(key)
                    if value is not None and not isinstance(value, datetime):
                        data[key] = datetime.fromisoformat(str(value))
                data["operation_type"] = OperationType(data["operation_type"])
                data["status"] = ReservationStatus(data["status"])
                data["allocation"] = [Allocation(**a) for a in data.get("allocation", [])]
                self.reservations[data["id"]] = CreditReservation(
                    **{k: data[k] for k in CreditReservation.__dataclass_fields__ if k in data}
                )
                reservation = self.reservations[data["id"]]
                if reservation.idempotency_key:
                    self.idempotency[reservation.idempotency_key] = reservation
            except (KeyError, TypeError, ValueError):
                continue
        try:
            ledger_rows = self.persistence.list_all("credit_ledger")
        except Exception:  # noqa: BLE001 - transient journal outage must not crash startup
            ledger_rows = []
        for data in ledger_rows:
            try:
                data = dict(data)
                value = data.get("created_at")
                if value is not None and not isinstance(value, datetime):
                    data["created_at"] = datetime.fromisoformat(str(value))
                data["source"] = FundingSource(data["source"])
                data["direction"] = LedgerDirection(data["direction"])
                entry = CreditLedgerEntry(
                    **{k: data[k] for k in CreditLedgerEntry.__dataclass_fields__ if k in data}
                )
                self.ledger.append(entry)
            except (KeyError, TypeError, ValueError):
                continue

    def _commit(self, writes):
        writes = [
            (collection, key, self._serialize(data))
            for collection, key, data in writes
        ]
        if self.persistence and hasattr(self.persistence, "atomic_commit"):
            self.persistence.atomic_commit(writes)
        elif self.persistence:
            for collection, key, data in writes:
                self.persistence.append(collection, key, data)

    @classmethod
    def _serialize(cls, value):
        if is_dataclass(value):
            return cls._serialize(asdict(value))
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, dict):
            return {key: cls._serialize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._serialize(item) for item in value]
        return value

    def create_cost_profile(self, operation_type, credit_cost, *, enabled=True):
        with self.lock:
            op = OperationType(operation_type)
            current = self.profiles.get(op)
            version = (current.version + 1) if current else 1
            profile = CostProfile(op, version, credit_cost, enabled=enabled)
            self.profiles[op] = profile
            return profile

    def expire(self, now=None):
        now = now or self.clock()
        expired = 0
        with self.lock:
            for grant in self.grants.values():
                if (
                    grant.expires_at
                    and grant.expires_at <= now
                    and grant.remaining_amount > 0
                    and grant.reserved_amount == 0
                ):
                    amount = grant.remaining_amount
                    grant.remaining_amount = 0
                    grant.exhausted_at = now
                    entry = CreditLedgerEntry(
                            str(uuid4()),
                            grant.user_id,
                            LedgerDirection.EXPIRE,
                            amount,
                            grant.source,
                            f"expire:{grant.id}",
                            grant_id=grant.id,
                            reason_code="GRANT_EXPIRED",
                        )
                    self._commit([("credit_grants", grant.id, grant.__dict__), ("credit_ledger", entry.id, entry.__dict__)])
                    self.ledger.append(entry)
                    expired += 1
            for reservation in self.reservations.values():
                if (
                    reservation.status == ReservationStatus.RESERVED
                    and reservation.expires_at <= now
                ):
                    self.release(reservation.id, "RESERVATION_TIMEOUT")
                    reservation.status = ReservationStatus.EXPIRED
                    self._commit([
                        ("credit_reservations", reservation.id, reservation.__dict__)
                    ])
                    expired += 1
        return expired

    def audit(self):
        with self.lock:
            for grant in self.grants.values():
                if grant.remaining_amount < 0 or grant.reserved_amount < 0:
                    raise FundingError("LEDGER_INVARIANT_VIOLATION")
            for reservation in self.reservations.values():
                if sum(a.amount for a in reservation.allocation) != reservation.requested_amount:
                    raise FundingError("LEDGER_INVARIANT_VIOLATION")
        return {
            "grants": len(self.grants),
            "reservations": len(self.reservations),
            "ledger_entries": len(self.ledger),
            "status": "OK",
        }

    def materialize_allowance(self, user_id, amount=3):
        with self.lock:
            key = (user_id, "FREE_ALLOWANCE")
            if key not in self.idempotency:
                self.grant(
                    user_id, FundingSource.FREE_ALLOWANCE, amount, source_reference="allowance:v1"
                )
                self.idempotency[key] = True

    def grant(self, user_id, source, amount, source_reference=None, idempotency_key=None):
        if amount < 0:
            raise FundingError("CREDIT_AMOUNT_MUST_BE_NON_NEGATIVE")
        with self.lock:
            if idempotency_key and idempotency_key in self.idempotency:
                return self.idempotency[idempotency_key]
            g = CreditGrant(
                str(uuid4()), user_id, source, amount, amount, source_reference=source_reference
            )
            entry = CreditLedgerEntry(
                    str(uuid4()),
                    user_id,
                    LedgerDirection.GRANT,
                    amount,
                    source,
                    idempotency_key or g.id,
                    grant_id=g.id,
                )
            self._commit([("credit_grants", g.id, g.__dict__), ("credit_ledger", entry.id, entry.__dict__)])
            self.grants[g.id] = g
            self.ledger.append(entry)
            if idempotency_key:
                self.idempotency[idempotency_key] = g
            return g

    def quote(self, user_id, operation_type):
        op = OperationType(operation_type)
        p = self.profiles.get(op)
        if not p or not p.enabled:
            raise FundingError("COST_PROFILE_UNAVAILABLE")
        self.materialize_allowance(user_id)
        available = sum(
            g.remaining_amount - g.reserved_amount
            for g in self.grants.values()
            if g.user_id == user_id and (not g.expires_at or g.expires_at > self.clock())
        )
        return {
            "quote_id": str(uuid4()),
            "operation_type": op,
            "cost_profile_version": p.version,
            "required_credits": p.credit_cost,
            "currently_fundable": available >= p.credit_cost,
            "available_credits": available,
            "additional_credits_required": max(0, p.credit_cost - available),
            "rewarded_ad_available": available < p.credit_cost,
            "premium_option_available": False,
            "expires_at": self.clock().isoformat(),
        }

    def reserve(self, user_id, operation_type, operation_request_id, idempotency_key):
        with self.lock:
            if idempotency_key in self.idempotency:
                return self.idempotency[idempotency_key]
            q = self.quote(user_id, operation_type)
            need = q["required_credits"]
            if self.persistence and hasattr(self.persistence, "transactional_reservation"):
                try:
                    data = self.persistence.transactional_reservation(
                        user_id,
                        operation_request_id,
                        idempotency_key,
                        need,
                        q["cost_profile_version"],
                        str(OperationType(operation_type)),
                        self.clock() + __import__("datetime").timedelta(minutes=15),
                    )
                except ValueError as exc:
                    raise FundingError(str(exc)) from exc
                data["operation_type"] = OperationType(data["operation_type"])
                data["status"] = ReservationStatus(data["status"])
                data["allocation"] = [Allocation(**a) for a in data["allocation"]]
                reservation = CreditReservation(
                    **{k: data[k] for k in CreditReservation.__dataclass_fields__ if k in data}
                )
                self.reservations[reservation.id] = reservation
                return reservation
            # Explicitly earned/promotional balances are consumed before the
            # free allowance. The allowance remains a durable fallback and
            # must not unexpectedly hide paid/rewarded provenance.
            source_priority = {
                FundingSource.REWARDED_AD: 0,
                FundingSource.PROMOTIONAL: 1,
                FundingSource.PREMIUM: 2,
                FundingSource.FREE_ALLOWANCE: 3,
            }
            grants = sorted(
                [
                    g
                    for g in self.grants.values()
                    if g.user_id == user_id and g.remaining_amount - g.reserved_amount > 0
                ],
                    key=lambda g: (source_priority.get(g.source, 99), g.expires_at or datetime.max.replace(tzinfo=UTC), g.created_at, g.id),
            )
            alloc = []
            left = need
            for g in grants:
                n = min(left, g.remaining_amount - g.reserved_amount)
                g.reserved_amount += n
                alloc.append(Allocation(g.id, n, g.source))
                left -= n
                if not left:
                    break
            if left:
                for a in alloc:
                    self.grants[a.grant_id].reserved_amount -= a.amount
                raise FundingError("FUNDING_REQUIRED")
            r = CreditReservation(
                str(uuid4()),
                user_id,
                OperationType(operation_type),
                q["cost_profile_version"],
                need,
                ReservationStatus.RESERVED,
                alloc,
                operation_request_id,
                idempotency_key,
            )
            self.reservations[r.id] = r
            writes = [("credit_reservations", r.id, r.__dict__)]
            self.idempotency[idempotency_key] = r
            for a in alloc:
                entry = CreditLedgerEntry(
                    str(uuid4()),
                    user_id,
                    LedgerDirection.RESERVE,
                    a.amount,
                    a.funding_source,
                    idempotency_key,
                    grant_id=a.grant_id,
                    reservation_id=r.id,
                    operation_request_id=operation_request_id,
                )
                self.ledger.append(entry)
                writes.append(("credit_ledger", entry.id, entry.__dict__))
            self._commit(writes)
            return r

    def consume(self, reservation_id, execution_id):
        with self.lock:
            if self.persistence and hasattr(self.persistence, "transactional_transition"):
                reservation = self.reservations.get(reservation_id)
                if not reservation:
                    raise FundingError("CREDIT_RESERVATION_NOT_FOUND")
                try:
                    self.persistence.transactional_transition(
                        reservation_id, reservation.user_id, "consume", execution_id
                    )
                except ValueError as exc:
                    raise FundingError(str(exc)) from exc
                if reservation_id in self.reservations:
                    self.reservations[reservation_id].status = ReservationStatus.CONSUMED
                return self.reservations.get(reservation_id)
            r = self.reservations.get(reservation_id)
            if not r:
                raise FundingError("CREDIT_RESERVATION_NOT_FOUND")
            if r.status == ReservationStatus.CONSUMED:
                return r
            if r.status != ReservationStatus.RESERVED:
                raise FundingError("CREDIT_RESERVATION_NOT_CONSUMABLE")
            for a in r.allocation:
                g = self.grants[a.grant_id]
                g.remaining_amount -= a.amount
                g.reserved_amount -= a.amount
                entry = CreditLedgerEntry(
                    str(uuid4()),
                    r.user_id,
                    LedgerDirection.CONSUME,
                    a.amount,
                    a.funding_source,
                    execution_id,
                    grant_id=g.id,
                    reservation_id=r.id,
                )
                self.ledger.append(entry)
                self._commit(
                    [
                        ("credit_grants", g.id, g.__dict__),
                        ("credit_reservations", r.id, r.__dict__),
                        ("credit_ledger", entry.id, entry.__dict__),
                    ]
                )
            r.status = ReservationStatus.CONSUMED
            r.consumed_at = self.clock()
            return r

    def release(self, reservation_id, reason="RELEASED"):
        with self.lock:
            if self.persistence and hasattr(self.persistence, "transactional_transition"):
                existing = self.reservations.get(reservation_id)
                if not existing:
                    raise FundingError("CREDIT_RESERVATION_NOT_FOUND")
                try:
                    self.persistence.transactional_transition(
                        reservation_id, existing.user_id, "release", reason
                    )
                except ValueError as exc:
                    raise FundingError(str(exc)) from exc
                existing.status = ReservationStatus.RELEASED
                return existing
            r = self.reservations.get(reservation_id)
            if not r:
                raise FundingError("CREDIT_RESERVATION_NOT_FOUND")
            if r.status == ReservationStatus.RELEASED:
                return r
            if r.status != ReservationStatus.RESERVED:
                raise FundingError("CREDIT_RESERVATION_NOT_RELEASABLE")
            for a in r.allocation:
                g = self.grants[a.grant_id]
                g.reserved_amount -= a.amount
                entry = CreditLedgerEntry(
                    str(uuid4()),
                    r.user_id,
                    LedgerDirection.RELEASE,
                    a.amount,
                    a.funding_source,
                    reason,
                    grant_id=g.id,
                    reservation_id=r.id,
                )
                self.ledger.append(entry)
                self._commit(
                    [
                        ("credit_grants", g.id, g.__dict__),
                        ("credit_reservations", r.id, r.__dict__),
                        ("credit_ledger", entry.id, entry.__dict__),
                    ]
                )
            r.status = ReservationStatus.RELEASED
            r.released_at = self.clock()
            return r
