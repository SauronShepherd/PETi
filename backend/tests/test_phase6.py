from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal
from threading import Barrier

import pytest
from app.phase6 import CareStatus, Phase6Service, SourceClass, convert


class Pets:
    def get(self, owner, pet):
        return object() if owner == "u1" and pet == "p1" else None


class Store:
    def __init__(self):
        self.records = {}

    def put(self, collection, record):
        self.records.setdefault(collection, {})[record.id] = record

    def put_user(self, collection, user_id, record):
        self.records.setdefault(collection, {})[getattr(record, "id", user_id)] = {
            **record.__dict__,
            "user_id": user_id,
        }

    def all(self, collection):
        return [
            record.__dict__ if hasattr(record, "__dict__") else record
            for record in self.records.get(collection, {}).values()
        ]


def measurement(**overrides):
    value = {
        "measurement_type": "WEIGHT",
        "original_value": "22.4",
        "original_unit": "lb",
        "source_class": SourceClass.MEASURED,
        "measured_at": datetime.now(UTC),
    }
    value.update(overrides)
    return value


def test_golden_conversions_and_original_value():
    assert convert("22.4", "lb") == (Decimal("10.160"), "kg")
    service = Phase6Service()
    record = service.measurement("u1", "p1", measurement(), "m1", Pets())
    assert record.original_value == "22.4"
    assert record.original_unit == "lb"
    assert record.normalized_unit == "kg"


def test_golden_conversions_cover_temperature_and_round_trip_precision():
    assert convert("212", "F") == (Decimal("100.000"), "°C")
    assert convert("0", "°C") == (Decimal("32.000"), "°F")
    kg, unit = convert("10", "lb")
    assert convert(str(kg), unit) == (Decimal("10.000"), "lb")


def test_ai_estimates_and_cross_user_are_rejected():
    service = Phase6Service()
    with pytest.raises(ValueError, match="AI_SOURCE"):
        service.measurement("u1", "p1", measurement(source_class="AI_ESTIMATED"), "m1", Pets())
    with pytest.raises(ValueError, match="PET_NOT_FOUND"):
        service.measurement("u2", "p1", measurement(), "m2", Pets())


def test_notification_controls_reject_truthy_string_values():
    service = Phase6Service()
    with pytest.raises(ValueError, match="NOTIFICATION_ENABLED_FLAG_INVALID"):
        service.create_care(
            "u1", "p1", {"category": "CUSTOM", "title": "Brush", "due_at": datetime.now(UTC), "notification_enabled": "false"},
            "notification-type", Pets(),
        )
    with pytest.raises(ValueError, match="NOTIFICATION_ENABLED_FLAG_INVALID"):
        service.update_preferences("u1", {"care_notifications_enabled": "false"})
    assert "u1" not in service.notification_preferences


def test_remove_owner_data_purges_care_graph_and_measurements():
    service = Phase6Service()
    service.measurement("u1", "p1", measurement(), "m1", Pets())
    service.create_care(
        "u1", "p1", {"category": "CUSTOM", "title": "Brush", "due_at": datetime.now(UTC)}, "c1", Pets()
    )
    service.preferences("u1")
    result = service.remove_owner_data("u1")
    assert result == {"measurements": 1, "care_items": 1, "care_occurrences": 1, "notification_preferences": 1, "idempotency": 2}
    assert all(item.owner_user_id != "u1" for item in service.measurements.values())
    assert all(item.owner_user_id != "u1" for item in service.care.values())
    assert all(item.owner_user_id != "u1" for item in service.occurrences.values())


def test_recurring_care_preserves_completion_and_creates_next_occurrence():
    service = Phase6Service()
    care = service.create_care(
        "u1",
        "p1",
        {"category": "CUSTOM", "title": "Brush", "due_at": datetime.now(UTC), "repeat_days": 7},
        "c1",
        Pets(),
    )
    original = next(iter(service.occurrences.values()))
    completed = service.action("u1", original.id, "complete", Pets())
    assert completed.status == CareStatus.COMPLETED
    assert len(service.occurrences) == 2
    assert any(
        item.care_id == care.id and item.status == CareStatus.ACTIVE
        for item in service.occurrences.values()
    )


def test_notification_permission_and_dedupe_do_not_change_care_state():
    service = Phase6Service()
    service.create_care(
        "u1",
        "p1",
        {"category": "CUSTOM", "title": "Brush", "due_at": datetime(2020, 1, 1, tzinfo=UTC)},
        "c1",
        Pets(),
    )
    service.register_device(
        "u1",
        {
            "installation_id": "i1",
            "fcm_token": "secret",
            "notifications_permission_state": "GRANTED",
        },
    )
    sent = service.dispatch_due(sender=lambda token, payload: "message-1")
    assert len(sent) == 1
    assert len(service.dispatch_due(sender=lambda token, payload: "message-2")) == 0
    assert next(iter(service.occurrences.values())).status == CareStatus.ACTIVE
    service.update_preferences("u1", {"care_notifications_enabled": False})
    assert service.dispatch_due() == []


def test_concurrent_notification_dispatch_sends_once():
    service = Phase6Service()
    service.create_care(
        "u1", "p1", {"category": "CUSTOM", "title": "Brush", "due_at": datetime(2020, 1, 1, tzinfo=UTC)},
        "concurrent-notification", Pets(),
    )
    service.register_device(
        "u1", {"installation_id": "concurrent", "fcm_token": "secret", "notifications_permission_state": "GRANTED"}
    )
    barrier = Barrier(2)
    calls = []

    def sender(token, payload):
        calls.append(payload["occurrence_id"])
        return "message"

    def dispatch():
        barrier.wait()
        return service.dispatch_due(sender=sender)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: dispatch(), range(2)))

    assert sum(len(result) for result in results) == 1
    assert len(calls) == 1


def test_concurrent_occurrence_action_is_idempotent():
    service = Phase6Service()
    care = service.create_care(
        "u1", "p1", {"category": "CUSTOM", "title": "Brush", "due_at": datetime(2020, 1, 1, tzinfo=UTC), "repeat_frequency": "DAILY"},
        "concurrent-action", Pets(),
    )
    occurrence = next(item for item in service.occurrences.values() if item.care_id == care.id)
    barrier = Barrier(2)

    def act():
        barrier.wait()
        return service.action("u1", occurrence.id, "complete", Pets(), idempotency_key="action-once")

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: act(), range(2)))

    assert all(item.id == occurrence.id for item in results)
    assert sum(item.care_id == care.id for item in service.occurrences.values()) == 2


def test_overdue_status_is_independent_of_notification_permission():
    service = Phase6Service()
    service.create_care(
        "u1", "p1", {"category": "CUSTOM", "title": "Brush", "due_at": datetime(2020, 1, 1, tzinfo=UTC)},
        "permission-independent", Pets(),
    )
    occurrence = next(iter(service.occurrences.values()))
    assert service.occurrence_status(occurrence, datetime(2020, 1, 2, tzinfo=UTC)) == "OVERDUE"
    service.register_device("u1", {"installation_id": "denied", "fcm_token": "secret", "notifications_permission_state": "DENIED"})
    assert service.occurrence_status(occurrence, datetime(2020, 1, 2, tzinfo=UTC)) == "OVERDUE"


def test_account_deletion_removes_device_tokens_and_deliveries():
    service = Phase6Service()
    service.register_device("u1", {"installation_id": "i1", "fcm_token": "secret"})
    service.register_device("u2", {"installation_id": "i2", "fcm_token": "keep"})
    assert service.remove_device_registrations("u1") == 1
    assert all(device.user_id != "u1" for device in service.devices.values())
    assert any(device.fcm_token == "keep" for device in service.devices.values())


def test_phase6_hydrates_after_process_restart():
    store = Store()
    first = Phase6Service(store)
    first.measurement("u1", "p1", measurement(), "m1", Pets())
    first.create_care(
        "u1",
        "p1",
        {"category": "CUSTOM", "title": "Brush", "due_at": datetime.now(UTC)},
        "c1",
        Pets(),
    )
    measurement_row = next(iter(store.records["measurements"].values()))
    measurement_row.measured_at = measurement_row.measured_at.isoformat()
    measurement_row.recorded_at = measurement_row.recorded_at.isoformat()
    care_row = next(iter(store.records["care_items"].values()))
    care_row.due_at = care_row.due_at.isoformat()
    restarted = Phase6Service(store)
    assert len(restarted.measurements) == 1
    assert len(restarted.care) == 1
    assert len(restarted.occurrences) == 1
    assert isinstance(next(iter(restarted.measurements.values())).measured_at, datetime)
    assert isinstance(next(iter(restarted.care.values())).due_at, datetime)


def test_phase6_skips_one_malformed_timestamp_without_aborting_hydration():
    source = Phase6Service()
    valid = source.measurement("u1", "p1", measurement(), "good", Pets())

    class MixedStore:
        def all(self, collection):
            if collection == "measurements":
                return [
                    {**valid.__dict__, "id": "bad", "measured_at": "not-a-date"},
                    {**valid.__dict__, "measured_at": datetime(2026, 8, 26, tzinfo=UTC).isoformat()},
                ]
            return []

    restarted = Phase6Service(MixedStore())
    assert "bad" not in restarted.measurements
    assert len(restarted.measurements) == 1


def test_timeline_filters_and_paginates_deterministically():
    service = Phase6Service()
    older = datetime(2020, 1, 1, tzinfo=UTC)
    newer = datetime(2020, 1, 2, tzinfo=UTC)
    service.measurement("u1", "p1", measurement(measured_at=older), "m1", Pets())
    service.measurement("u1", "p1", measurement(measured_at=newer), "m2", Pets())
    items = service.timeline("u1", "p1", item_type="WEIGHT_MEASUREMENT", limit=1)
    assert len(items) == 1
    assert items[0]["occurred_at"] == newer
    assert service.timeline("u1", "p1", before=newer, limit=10)[0]["occurred_at"] == older


def test_injectable_clock_controls_recorded_and_delivery_times():
    fixed = datetime(2024, 1, 1, tzinfo=UTC)
    service = Phase6Service(clock=lambda: fixed)
    record = service.measurement("u1", "p1", measurement(), "clock-1", Pets())
    assert record.recorded_at == fixed
    prefs = service.preferences("u1")
    assert prefs.updated_at == fixed
