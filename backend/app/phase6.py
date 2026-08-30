"""Phase 6 canonical structured-care services.

The service is deliberately provider- and ad-free.  The repository shape is
small and injectable so the same contracts can be backed by Firestore later.
"""

import calendar
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from hashlib import sha256
from threading import RLock
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class MeasurementType(StrEnum):
    WEIGHT = "WEIGHT"
    TEMPERATURE = "TEMPERATURE"


class SourceClass(StrEnum):
    MEASURED = "MEASURED"
    DOCUMENTED = "DOCUMENTED"
    OWNER_REPORTED = "OWNER_REPORTED"
    AI_ESTIMATED = "AI_ESTIMATED"


class CareStatus(StrEnum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    CANCELED = "CANCELED"
    RESCHEDULED = "RESCHEDULED"


WEIGHT_UNITS = {"kg", "lb"}
TEMP_UNITS = {"C", "F", "°C", "°F"}
CARE_CATEGORIES = {
    "VACCINATION",
    "PARASITE_PREVENTION",
    "APPOINTMENT",
    "MEDICATION_OR_FOLLOWUP",
    "BODY_CHECK",
    "CUSTOM",
}


def firebase_fcm_sender(token, payload):
    """Send the minimal Phase 6 data payload through Firebase Admin FCM."""
    from firebase_admin import messaging

    message = messaging.Message(
        token=token,
        data={"occurrence_id": str(payload["occurrence_id"])},
    )
    return messaging.send(message)


def _now():
    return datetime.now(UTC)


def _q(v):
    return Decimal(str(v)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def convert(value, unit):
    v, u = Decimal(str(value)), unit
    if u == "lb":
        return _q(v * Decimal("0.45359237")), "kg"
    if u == "kg":
        return _q(v * Decimal("2.2046226218")), "lb"
    if u in {"F", "°F"}:
        return _q((v - 32) * Decimal(5) / Decimal(9)), "°C"
    if u in {"C", "°C"}:
        return _q(v * Decimal(9) / Decimal(5) + 32), "°F"
    raise ValueError("MEASUREMENT_UNIT_UNSUPPORTED")


@dataclass
class Measurement:
    id: str
    owner_user_id: str
    animal_id: str
    measurement_type: str
    source_class: str
    original_value: str
    original_unit: str
    normalized_value: str
    normalized_unit: str
    measured_at: datetime
    recorded_at: datetime
    notes: str | None = None
    deleted_at: datetime | None = None
    source_document_id: str | None = None


@dataclass
class CareItem:
    id: str
    owner_user_id: str
    animal_id: str
    category: str
    title: str
    due_at: datetime
    repeat_days: int | None = None
    notes: str | None = None
    notification_enabled: bool = True
    deleted_at: datetime | None = None
    timezone: str = "UTC"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    repeat_frequency: str = "ONCE"
    repeat_interval: int = 1
    day_of_month: int | None = None


@dataclass
class CareOccurrence:
    id: str
    care_id: str
    owner_user_id: str
    animal_id: str
    due_at: datetime
    status: str = CareStatus.ACTIVE
    completed_at: datetime | None = None
    notes: str | None = None
    skipped_at: datetime | None = None
    rescheduled_from: datetime | None = None
    rescheduled_to: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class NotificationPreferences:
    user_id: str
    care_notifications_enabled: bool = True
    timezone: str = "UTC"
    quiet_hours: dict | None = None
    updated_at: datetime | None = None


@dataclass
class DeviceRegistration:
    id: str
    user_id: str
    installation_id: str
    fcm_token: str
    platform: str
    app_version: str
    notifications_permission_state: str
    active: bool = True
    last_seen_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class NotificationDelivery:
    id: str
    user_id: str
    occurrence_id: str
    device_registration_id: str
    channel: str
    scheduled_for: datetime
    attempted_at: datetime | None = None
    provider_message_id: str | None = None
    status: str = "PENDING"
    failure_code: str | None = None


class Phase6Service:
    def __init__(self, store=None, clock=None, analytics=None):
        self.store = store
        self.clock = clock or _now
        self.analytics = analytics
        self.measurements = {}
        self.care = {}
        self.occurrences = {}
        self.idempotency = {}
        self.notification_preferences = {}
        self.devices = {}
        self.deliveries = {}
        self.local_fcm_inbox = []
        self.lock = RLock()
        self._hydrate()

    def _now(self):
        return self.clock()

    def _hydrate(self):
        if self.store is None or not hasattr(self.store, "all"):
            return
        def hydrate_rows(collection, datetime_fields):
            rows = []
            try:
                stored_rows = self.store.all(collection)
            except Exception:  # noqa: BLE001 - one unavailable collection must not crash startup
                stored_rows = []
            for raw in stored_rows:
                try:
                    data = dict(raw)
                    for key in datetime_fields:
                        value = data.get(key)
                        if value is not None and not isinstance(value, datetime):
                            data[key] = datetime.fromisoformat(str(value))
                except (TypeError, ValueError):
                    continue
                rows.append(data)
            return rows

        for data in hydrate_rows("measurements", ("measured_at", "recorded_at", "deleted_at")):
            try:
                self.measurements[data["id"]] = Measurement(**data)
            except (KeyError, TypeError, ValueError):
                continue
        for data in hydrate_rows("care_items", ("due_at", "deleted_at", "created_at", "updated_at")):
            try:
                self.care[data["id"]] = CareItem(**data)
            except (KeyError, TypeError, ValueError):
                continue
        for data in hydrate_rows("care_occurrences", ("due_at", "completed_at", "skipped_at", "rescheduled_from", "rescheduled_to", "created_at", "updated_at")):
            try:
                self.occurrences[data["id"]] = CareOccurrence(**data)
            except (KeyError, TypeError, ValueError):
                continue
        for data in hydrate_rows("notification_preferences", ("updated_at",)):
            user_id = data.pop("user_id", data.get("id"))
            data.pop("id", None)
            try:
                self.notification_preferences[user_id] = NotificationPreferences(user_id, **data)
            except (KeyError, TypeError, ValueError):
                continue
        for data in hydrate_rows("device_registrations", ("last_seen_at", "created_at", "updated_at")):
            try:
                self.devices[data["id"]] = DeviceRegistration(**data)
            except (KeyError, TypeError, ValueError):
                continue
        for data in hydrate_rows("notification_deliveries", ("scheduled_for", "attempted_at")):
            try:
                key = f"{data['occurrence_id']}:DUE:{data['device_registration_id']}"
                self.deliveries[key] = NotificationDelivery(**data)
            except (KeyError, TypeError, ValueError):
                continue
        try:
            idempotency_rows = self.store.all("phase6_idempotency")
        except Exception:  # noqa: BLE001 - unavailable idempotency state must not crash startup
            idempotency_rows = []
        for data in idempotency_rows:
            try:
                self.idempotency[(data["owner_user_id"], data["kind"], data["key"])] = (
                    data["fingerprint"], data["record_id"],
                )
            except (KeyError, TypeError):
                continue

    def _persist(self, collection, record):
        if self.store is not None:
            self.store.put(collection, record)

    def _record_event(self, event, owner, **fields):
        if self.analytics is not None:
            self.analytics.record(event, user_id=owner, **fields)

    def _persist_idempotency(self, owner, kind, key, fingerprint, record_id):
        if self.store is not None and hasattr(self.store, "put_raw"):
            self.store.put_raw(
                "phase6_idempotency",
                sha256(f"{owner}:{kind}:{key}".encode()).hexdigest(),
                {
                    "owner_user_id": owner,
                    "kind": kind,
                    "key": key,
                    "fingerprint": fingerprint,
                    "record_id": record_id,
                },
            )

    @staticmethod
    def _occurrence_id(care_id, due_at):
        return sha256(f"{care_id}:{due_at.isoformat()}".encode()).hexdigest()[:32]

    def _owned_pet(self, pets, owner, pet):
        if not pets.get(owner, pet):
            raise ValueError("PET_NOT_FOUND")

    def measurement(self, owner, pet, body, key, pets):
        self._owned_pet(pets, owner, pet)
        if not key:
            raise ValueError("IDEMPOTENCY_KEY_REQUIRED")
        fp = sha256(repr(sorted(body.items())).encode()).hexdigest()
        idem = (owner, "measurement", key)
        with self.lock:
            if idem in self.idempotency:
                if self.idempotency[idem][0] != fp:
                    raise ValueError("IDEMPOTENCY_KEY_REUSE_CONFLICT")
                return self.measurements[self.idempotency[idem][1]]
            try:
                typ = MeasurementType(body["measurement_type"])
            except ValueError as exc:
                raise ValueError("MEASUREMENT_TYPE_UNSUPPORTED") from exc
            unit = body["original_unit"]
            try:
                value = Decimal(str(body["original_value"]).strip().replace(",", "."))
            except ArithmeticError as exc:
                raise ValueError("MEASUREMENT_VALUE_INVALID") from exc
            if not value.is_finite() or value <= 0:
                raise ValueError("MEASUREMENT_VALUE_INVALID")
            if typ == MeasurementType.WEIGHT and unit not in WEIGHT_UNITS:
                raise ValueError("MEASUREMENT_UNIT_UNSUPPORTED")
            if typ == MeasurementType.TEMPERATURE and unit not in TEMP_UNITS:
                raise ValueError("MEASUREMENT_UNIT_UNSUPPORTED")
            source = body.get("source_class", SourceClass.MEASURED)
            try:
                source = SourceClass(source)
            except ValueError as exc:
                raise ValueError("MEASUREMENT_SOURCE_INVALID") from exc
            if source == SourceClass.AI_ESTIMATED:
                raise ValueError("MEASUREMENT_AI_SOURCE_NOT_CLIENT_CREATABLE")
            norm, nunit = convert(value, unit)
            m = Measurement(
                uuid4().hex,
                owner,
                pet,
                typ,
                source,
                str(value),
                unit,
                str(norm),
                nunit,
                body.get("measured_at", self._now()),
                self._now(),
                body.get("notes"),
                source_document_id=body.get("source_document_id"),
            )
            self.measurements[m.id] = m
            self._persist("measurements", m)
            self.idempotency[idem] = (fp, m.id)
            self._persist_idempotency(owner, "measurement", key, fp, m.id)
            self._record_event("measurement_logged", owner, check_id=m.id)
            return m

    def create_care(self, owner, pet, body, key, pets):
        self._owned_pet(pets, owner, pet)
        if not key:
            raise ValueError("IDEMPOTENCY_KEY_REQUIRED")
        idem = (owner, "care", key)
        fp = sha256(repr(sorted(body.items())).encode()).hexdigest()
        with self.lock:
            if idem in self.idempotency:
                if self.idempotency[idem][0] not in {"", fp}:
                    raise ValueError("IDEMPOTENCY_KEY_REUSE_CONFLICT")
                return self.care[self.idempotency[idem][1]]
            due_at = body["due_at"]
            notification_enabled = body.get("notification_enabled", True)
            if not isinstance(notification_enabled, bool):
                raise ValueError("NOTIFICATION_ENABLED_FLAG_INVALID")  # noqa: TRY004
            if due_at.tzinfo is None:
                due_at = due_at.replace(tzinfo=UTC)
            created_at = self._now()
            c = CareItem(
                uuid4().hex,
                owner,
                pet,
                body["category"],
                body["title"],
                due_at,
                body.get("repeat_days"),
                body.get("notes"),
                notification_enabled,
                timezone=body.get("timezone", "UTC"),
                created_at=created_at,
                updated_at=created_at,
                repeat_frequency=body.get("repeat_frequency", "ONCE"),
                repeat_interval=body.get("repeat_interval", 1),
                day_of_month=body.get("day_of_month"),
            )
            if c.category not in CARE_CATEGORIES or c.repeat_frequency not in {"ONCE", "DAILY", "WEEKLY", "MONTHLY", "CUSTOM_INTERVAL"}:
                raise ValueError("CARE_RULE_INVALID")
            if not c.timezone or c.repeat_interval < 1 or (c.day_of_month is not None and not 1 <= c.day_of_month <= 31):
                raise ValueError("CARE_RULE_INVALID")
            try:
                ZoneInfo(c.timezone)
            except ZoneInfoNotFoundError as exc:
                raise ValueError("CARE_RULE_INVALID") from exc
            self.care[c.id] = c
            self._persist("care_items", c)
            created_at = self._now()
            o = CareOccurrence(
                self._occurrence_id(c.id, c.due_at),
                c.id,
                owner,
                pet,
                c.due_at,
                created_at=created_at,
                updated_at=created_at,
            )
            self.occurrences[o.id] = o
            self._persist("care_occurrences", o)
            self.idempotency[idem] = (fp, c.id)
            self._persist_idempotency(owner, "care", key, fp, c.id)
            self._record_event("care_created", owner, check_id=c.id)
            return c

    def update_care(self, owner, care_id, values):
        care = self.care.get(care_id)
        if not care or care.owner_user_id != owner or care.deleted_at:
            raise ValueError("CARE_NOT_FOUND")
        schedule_changed = any(
            field in values and getattr(care, field) != values[field]
            for field in ("due_at", "repeat_days", "timezone", "repeat_frequency", "repeat_interval", "day_of_month")
        )
        for field in ("category", "title", "notes", "repeat_days", "notification_enabled", "due_at", "timezone", "repeat_frequency", "repeat_interval", "day_of_month"):
            if field in values:
                setattr(care, field, values[field])
        if care.due_at.tzinfo is None:
            care.due_at = care.due_at.replace(tzinfo=UTC)
        if (
            care.category not in CARE_CATEGORIES
            or care.repeat_frequency not in {"ONCE", "DAILY", "WEEKLY", "MONTHLY", "CUSTOM_INTERVAL"}
            or not care.timezone
            or care.repeat_interval < 1
            or (care.day_of_month is not None and not 1 <= care.day_of_month <= 31)
        ):
            raise ValueError("CARE_RULE_INVALID")
        try:
            ZoneInfo(care.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("CARE_RULE_INVALID") from exc
        care.updated_at = self._now()
        if schedule_changed:
            for occurrence in self.occurrences.values():
                if occurrence.care_id == care_id and occurrence.status == CareStatus.ACTIVE:
                    occurrence.status = CareStatus.CANCELED
                    occurrence.updated_at = self._now()
                    self._persist("care_occurrences", occurrence)
            occurrence_id = self._occurrence_id(care.id, care.due_at)
            if occurrence_id not in self.occurrences:
                created_at = self._now()
                occurrence = CareOccurrence(
                    occurrence_id,
                    care.id,
                    care.owner_user_id,
                    care.animal_id,
                    care.due_at,
                    created_at=created_at,
                    updated_at=created_at,
                )
                self.occurrences[occurrence.id] = occurrence
                self._persist("care_occurrences", occurrence)
        self._persist("care_items", care)
        return care

    def measurement_trend(
        self,
        owner,
        pet,
        measurement_type=None,
        source_class=None,
        include_ai_estimates=False,
    ):
        records = [
            item
            for item in self.measurements.values()
            if item.owner_user_id == owner
            and item.animal_id == pet
            and not item.deleted_at
            and (measurement_type is None or item.measurement_type == measurement_type)
            and (source_class is None or item.source_class == source_class)
            and (include_ai_estimates or item.source_class != SourceClass.AI_ESTIMATED)
        ]
        records.sort(key=lambda item: (item.measured_at, item.id))
        previous = None
        trend = []
        for item in records:
            delta = None
            if previous is not None and previous.normalized_unit == item.normalized_unit:
                delta = str(Decimal(item.normalized_value) - Decimal(previous.normalized_value))
            trend.append(
                {
                    "id": item.id,
                    "measurement_type": item.measurement_type,
                    "measured_at": item.measured_at,
                    "original_value": item.original_value,
                    "original_unit": item.original_unit,
                    "normalized_value": item.normalized_value,
                    "normalized_unit": item.normalized_unit,
                    "source_class": item.source_class,
                    "delta": delta,
                }
            )
            previous = item
        return trend

    def _next_occurrence(self, care, occurrence):
        if not care or care.deleted_at or (not care.repeat_days and care.repeat_frequency == "ONCE"):
            return None
        due_at = self._next_due(care, occurrence.due_at)
        if due_at is None:
            return None
        occurrence_id = self._occurrence_id(care.id, due_at)
        if occurrence_id in self.occurrences:
            return self.occurrences[occurrence_id]
        created_at = self._now()
        next_occurrence = CareOccurrence(
            occurrence_id,
            care.id,
            occurrence.owner_user_id,
            occurrence.animal_id,
            due_at,
            created_at=created_at,
            updated_at=created_at,
        )
        self.occurrences[next_occurrence.id] = next_occurrence
        self._persist("care_occurrences", next_occurrence)
        return next_occurrence

    @staticmethod
    def _next_due(care, due_at):
        schedule_zone = ZoneInfo(care.timezone)
        original_zone = due_at.tzinfo or UTC
        local_due = due_at.replace(tzinfo=UTC) if due_at.tzinfo is None else due_at
        local_due = local_due.astimezone(schedule_zone)
        if care.repeat_days:
            next_local = local_due + timedelta(days=care.repeat_days)
            return next_local.astimezone(original_zone)
        if care.repeat_frequency == "DAILY":
            next_local = local_due + timedelta(days=care.repeat_interval)
            return next_local.astimezone(original_zone)
        if care.repeat_frequency == "WEEKLY":
            next_local = local_due + timedelta(days=7 * care.repeat_interval)
            return next_local.astimezone(original_zone)
        if care.repeat_frequency == "CUSTOM_INTERVAL":
            next_local = local_due + timedelta(days=care.repeat_interval)
            return next_local.astimezone(original_zone)
        if care.repeat_frequency == "MONTHLY":
            month = local_due.month - 1 + care.repeat_interval
            year = local_due.year + month // 12
            month = month % 12 + 1
            day = care.day_of_month or local_due.day
            day = min(day, calendar.monthrange(year, month)[1])
            return local_due.replace(year=year, month=month, day=day).astimezone(original_zone)
        return None

    def action(self, owner, occurrence_id, action, pets, due_at=None, idempotency_key=None):
        """Apply one occurrence action atomically under duplicate delivery."""
        with self.lock:
            return self._action(owner, occurrence_id, action, pets, due_at, idempotency_key)

    def _action(self, owner, occurrence_id, action, pets, due_at=None, idempotency_key=None):
        o = self.occurrences.get(occurrence_id)
        if not o or o.owner_user_id != owner:
            raise ValueError("CARE_OCCURRENCE_NOT_FOUND")
        if action not in {"complete", "skip", "reschedule"}:
            raise ValueError("CARE_OCCURRENCE_ACTION_INVALID")
        fingerprint = sha256(repr((occurrence_id, action, due_at)).encode()).hexdigest()
        idem = (owner, "occurrence_action", idempotency_key) if idempotency_key else None
        if idem and idem in self.idempotency:
            if self.idempotency[idem][0] != fingerprint:
                raise ValueError("IDEMPOTENCY_KEY_REUSE_CONFLICT")
            return self.occurrences[self.idempotency[idem][1]]
        if o.status in {CareStatus.COMPLETED, CareStatus.SKIPPED, CareStatus.CANCELED}:
            return o
        if action == "complete":
            completed_at = self._now()
            o.status = CareStatus.COMPLETED
            o.completed_at = completed_at
            o.updated_at = completed_at
            care = self.care.get(o.care_id)
            self._next_occurrence(care, o)
            self._record_event("care_completed", owner, check_id=o.id)
        elif action == "skip":
            skipped_at = self._now()
            o.status = CareStatus.SKIPPED
            o.skipped_at = skipped_at
            o.updated_at = skipped_at
            self._next_occurrence(self.care.get(o.care_id), o)
            self._record_event("care_skipped", owner, check_id=o.id)
        elif action == "reschedule":
            if due_at is None:
                raise ValueError("CARE_RESCHEDULE_INVALID")
            previous_due_at = o.due_at
            o.status = CareStatus.ACTIVE
            o.rescheduled_from = previous_due_at
            o.rescheduled_to = due_at
            o.due_at = due_at
            o.updated_at = self._now()
            self._record_event("care_rescheduled", owner, check_id=o.id)
        self._persist("care_occurrences", o)
        if idem:
            self.idempotency[idem] = (fingerprint, o.id)
            self._persist_idempotency(owner, "occurrence_action", idempotency_key, fingerprint, o.id)
        return o

    def occurrence_status(self, occurrence, now=None):
        if occurrence.status != CareStatus.ACTIVE:
            return occurrence.status
        now = now or self._now()
        if occurrence.due_at < now:
            return "OVERDUE"
        if occurrence.due_at == now:
            return "DUE"
        return "UPCOMING"

    def preferences(self, owner):
        value = self.notification_preferences.get(owner)
        if value is None:
            value = NotificationPreferences(owner, updated_at=self._now())
            self.notification_preferences[owner] = value
        return value

    def update_preferences(self, owner, values):
        if "care_notifications_enabled" in values and not isinstance(values["care_notifications_enabled"], bool):
            raise ValueError("NOTIFICATION_ENABLED_FLAG_INVALID")
        current = self.preferences(owner)
        if "care_notifications_enabled" in values:
            current.care_notifications_enabled = values["care_notifications_enabled"]
        if "timezone" in values:
            if not values["timezone"]:
                raise ValueError("NOTIFICATION_PREFERENCE_INVALID")
            try:
                ZoneInfo(values["timezone"])
            except (ZoneInfoNotFoundError, TypeError) as exc:
                raise ValueError("NOTIFICATION_PREFERENCE_INVALID") from exc
            current.timezone = values["timezone"]
        if "quiet_hours" in values:
            quiet_hours = values["quiet_hours"]
            if quiet_hours is not None:
                try:
                    for key in ("start", "end"):
                        hour, minute = map(int, str(quiet_hours[key]).split(":", 1))
                        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
                            raise ValueError
                    if set(quiet_hours) - {"start", "end"}:
                        raise ValueError
                except (KeyError, TypeError, ValueError) as exc:
                    raise ValueError("NOTIFICATION_PREFERENCE_INVALID") from exc
            current.quiet_hours = quiet_hours
        current.updated_at = self._now()
        if self.store is not None:
            self.store.put_user("notification_preferences", owner, current)
        return current

    def register_device(self, owner, values):
        token = values.get("fcm_token", "")
        if not token or not values.get("installation_id"):
            raise ValueError("NOTIFICATION_DEVICE_INVALID")
        existing = next(
            (
                d
                for d in self.devices.values()
                if d.user_id == owner and d.installation_id == values["installation_id"]
            ),
            None,
        )
        now = self._now()
        if existing:
            existing.fcm_token = token
            existing.app_version = values.get("app_version", existing.app_version)
            existing.notifications_permission_state = values.get(
                "notifications_permission_state", existing.notifications_permission_state
            )
            existing.active = True
            existing.last_seen_at = now
            existing.updated_at = now
            if self.store is not None:
                self.store.put_user("device_registrations", owner, existing)
            if existing.notifications_permission_state in {"GRANTED", "DENIED"}:
                self._record_event(
                    "notification_permission_result",
                    owner,
                    check_id=f"{existing.id}:{existing.notifications_permission_state}",
                    safety_state=existing.notifications_permission_state,
                )
            return existing
        device = DeviceRegistration(
            uuid4().hex,
            owner,
            values["installation_id"],
            token,
            values.get("platform", "WEB"),
            values.get("app_version", ""),
            values.get("notifications_permission_state", "UNKNOWN"),
            last_seen_at=now,
            created_at=now,
            updated_at=now,
        )
        self.devices[device.id] = device
        if self.store is not None:
            self.store.put_user("device_registrations", owner, device)
        if device.notifications_permission_state in {"GRANTED", "DENIED"}:
            self._record_event(
                "notification_permission_result",
                owner,
                check_id=f"{device.id}:{device.notifications_permission_state}",
                safety_state=device.notifications_permission_state,
            )
        return device

    def remove_device_registrations(self, owner: str) -> int:
        """Remove all notification tokens owned by an account.

        This is intentionally a hard delete: an account deletion must not
        leave reusable FCM credentials behind in memory or Firestore.
        """
        removed = [device for device in self.devices.values() if device.user_id == owner]
        for device in removed:
            self.devices.pop(device.id, None)
            if self.store is not None and hasattr(self.store, "delete"):
                self.store.delete("device_registrations", device.id)
        for delivery_id, delivery in list(self.deliveries.items()):
            if delivery.user_id == owner:
                self.deliveries.pop(delivery_id, None)
                if self.store is not None and hasattr(self.store, "delete"):
                    self.store.delete("notification_deliveries", delivery_id)
        return len(removed)

    def remove_owner_data(self, owner: str) -> dict[str, int]:
        """Remove all account-owned Phase 6 data during account deletion."""
        removed = {"measurements": 0, "care_items": 0, "care_occurrences": 0, "notification_preferences": 0, "idempotency": 0}
        for collection, values in (
            ("measurements", self.measurements),
            ("care_items", self.care),
            ("care_occurrences", self.occurrences),
        ):
            for item_id, item in list(values.items()):
                if getattr(item, "owner_user_id", None) != owner:
                    continue
                values.pop(item_id, None)
                if self.store is not None and hasattr(self.store, "delete"):
                    self.store.delete(collection, item_id)
                removed[collection] += 1
        if owner in self.notification_preferences:
            self.notification_preferences.pop(owner, None)
            if self.store is not None and hasattr(self.store, "delete"):
                self.store.delete("notification_preferences", owner)
            removed["notification_preferences"] = 1
        # Idempotency entries are account data and may point at objects just
        # removed above.  Leaving them behind can make a post-deletion retry
        # dereference deleted state or recreate an old logical operation.
        for idem, value in list(self.idempotency.items()):
            if idem[0] != owner:
                continue
            self.idempotency.pop(idem, None)
            if self.store is not None and hasattr(self.store, "delete"):
                digest = sha256(f"{owner}:{idem[1]}:{idem[2]}".encode()).hexdigest()
                self.store.delete("phase6_idempotency", digest)
            removed["idempotency"] += 1
        return removed

    def deactivate_device(self, owner, device_id):
        device = self.devices.get(device_id)
        if not device or device.user_id != owner:
            return False
        device.active = False
        device.updated_at = self._now()
        if self.store is not None:
            self.store.put_user("device_registrations", owner, device)
        return True

    def dispatch_due(self, now=None, sender=None):
        """Send due occurrences through an injected FCM sender with dedupe."""
        with self.lock:
            return self._dispatch_due(now, sender)

    def _dispatch_due(self, now=None, sender=None):
        now = now or self._now()
        sent = []
        for occurrence in self.occurrences.values():
            if occurrence.status != CareStatus.ACTIVE or occurrence.due_at > now:
                continue
            care = self.care.get(occurrence.care_id)
            if not care or care.deleted_at or not care.notification_enabled:
                continue
            prefs = self.preferences(occurrence.owner_user_id)
            if not prefs.care_notifications_enabled:
                continue
            if self._quiet_hours_active(prefs, now):
                continue
            for device in self.devices.values():
                if (
                    device.user_id != occurrence.owner_user_id
                    or not device.active
                    or device.notifications_permission_state == "DENIED"
                ):
                    continue
                dedupe = f"{occurrence.id}:DUE:{device.id}"
                if dedupe in self.deliveries:
                    continue
                delivery = NotificationDelivery(
                    uuid4().hex, device.user_id, occurrence.id, device.id, "FCM", occurrence.due_at
                )
                try:
                    message_id = (
                        sender(device.fcm_token, {"occurrence_id": occurrence.id})
                        if sender
                        else None
                    )
                    delivery.status = "SENT" if sender else "PENDING"
                    delivery.provider_message_id = message_id
                except Exception as exc:  # noqa: BLE001
                    failure_name = type(exc).__name__
                    terminal_failures = {"UnregisteredError", "InvalidArgumentError", "SenderIdMismatchError"}
                    delivery.status = "FAILED_FINAL" if failure_name in terminal_failures else "FAILED_RETRYABLE"
                    delivery.failure_code = failure_name
                delivery.attempted_at = now
                self.deliveries[dedupe] = delivery
                self._persist("notification_deliveries", delivery)
                if delivery.status == "SENT":
                    self._record_event("notification_delivered", occurrence.owner_user_id, check_id=occurrence.id)
                sent.append(delivery)
        return sent

    @staticmethod
    def _quiet_hours_active(preferences, now):
        if not preferences.quiet_hours:
            return False
        local_now = now.astimezone(ZoneInfo(preferences.timezone))
        start_hour, start_minute = map(int, preferences.quiet_hours["start"].split(":", 1))
        end_hour, end_minute = map(int, preferences.quiet_hours["end"].split(":", 1))
        current = local_now.hour * 60 + local_now.minute
        start = start_hour * 60 + start_minute
        end = end_hour * 60 + end_minute
        if start == end:
            return True
        return start <= current < end if start < end else current >= start or current < end

    def local_fcm_sender(self, token, payload):
        """Capture a local-only notification payload instead of calling FCM."""
        message_id = f"local-{len(self.local_fcm_inbox) + 1:06d}"
        self.local_fcm_inbox.append(
            {"message_id": message_id, "payload": {"occurrence_id": payload["occurrence_id"]}}
        )
        return message_id

    def local_fcm_inbox_snapshot(self):
        return list(self.local_fcm_inbox)

    def timeline(self, owner, pet, checks=(), item_type=None, before=None, after=None, limit=50):
        self._record_event("timeline_viewed", owner)
        items = []
        for m in self.measurements.values():
            if m.owner_user_id == owner and m.animal_id == pet and not m.deleted_at:
                items.append(
                    {
                        "id": "measurement:" + m.id,
                        "animal_id": pet,
                        "occurred_at": m.measured_at,
                        "recorded_at": m.recorded_at,
                        "item_type": m.measurement_type + "_MEASUREMENT",
                        "source_entity_type": "MEASUREMENT",
                        "source_entity_id": m.id,
                        "title": m.measurement_type.title(),
                        "summary": f"{m.original_value} {m.original_unit}",
                        "provenance": m.source_class,
                    }
                )
        for o in self.occurrences.values():
            if (
                o.owner_user_id == owner
                and o.animal_id == pet
                and o.status in {CareStatus.COMPLETED, CareStatus.SKIPPED}
            ):
                items.append(
                    {
                        "id": "care:" + o.id,
                        "animal_id": pet,
                        "occurred_at": o.completed_at or o.due_at,
                        "recorded_at": o.completed_at or o.due_at,
                        "item_type": "CARE_COMPLETION",
                        "source_entity_type": "CARE_OCCURRENCE",
                        "source_entity_id": o.id,
                        "title": "Care",
                        "summary": o.status,
                        "provenance": "OWNER_SCHEDULED",
                        "status": o.status,
                    }
                )
        items.extend(checks)
        items = sorted(items, key=lambda x: (x["occurred_at"], x["id"]), reverse=True)
        if item_type:
            grouped_types = {
                "CHECKS": {"PETI_CHECK"},
                "MEASUREMENTS": {"WEIGHT_MEASUREMENT", "TEMPERATURE_MEASUREMENT"},
                "CARE": {"CARE_OCCURRENCE", "CARE_COMPLETION"},
            }
            allowed = grouped_types.get(item_type)
            items = [item for item in items if item["item_type"] in allowed] if allowed else [item for item in items if item["item_type"] == item_type]
        if before:
            items = [item for item in items if item["occurred_at"] < before]
        if after:
            items = [item for item in items if item["occurred_at"] > after]
        return items[: max(1, min(limit, 100))]

    @staticmethod
    def public(x):
        return asdict(x)
