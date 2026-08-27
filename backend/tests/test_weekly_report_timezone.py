from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from app.reports.service import WeeklyReportService


def test_week_key_uses_account_timezone_boundary():
    instant = datetime(2026, 8, 23, 22, 30, tzinfo=UTC)  # Monday in Madrid
    key = WeeklyReportService.key("pet", instant, "Europe/Madrid")
    assert key.week_key == "2026-08-24"
    assert key.week_start.hour == 0
    assert key.week_start.tzinfo is not UTC


def test_invalid_timezone_fails_back_to_utc_deterministically():
    key = WeeklyReportService.key("pet", datetime(2026, 8, 24, tzinfo=UTC), "invalid/zone")
    assert key.week_key == "2026-08-24"
    assert key.timezone == "UTC"


def test_weekly_report_hydrates_serialized_timestamps():
    instant = datetime(2026, 8, 24, tzinfo=UTC)
    row = {
        "id": "report-1", "owner_user_id": "u", "animal_id": "pet", "week_key": "2026-08-24",
        "week_start": instant.isoformat(), "week_end": instant.isoformat(), "timezone": "UTC",
        "created_at": instant.isoformat(), "updated_at": instant.isoformat(), "deleted_at": None,
    }
    store = SimpleNamespace(all=lambda collection: [row] if collection == "weekly_reports" else [])
    service = WeeklyReportService(SimpleNamespace(), SimpleNamespace(), store=store)
    assert service.reports["report-1"].week_start == instant


def test_weekly_report_distinguishes_insufficient_stable_and_meaningful_change():
    pet = SimpleNamespace(id="pet")
    pets = SimpleNamespace(get=lambda owner, pet_id: pet if owner == "u" and pet_id == "pet" else None)
    phase6 = SimpleNamespace(timeline=lambda owner, pet_id, limit=100: [], measurements={})
    service = WeeklyReportService(pets, phase6)
    assert service.generate("u", "pet", datetime(2026, 8, 26, tzinfo=UTC)).change_state == "NOT_ENOUGH_DATA"

    first = SimpleNamespace(id="m1", owner_user_id="u", animal_id="pet", deleted_at=None,
                            measured_at=datetime(2026, 8, 24, tzinfo=UTC), normalized_value="10")
    second = SimpleNamespace(id="m2", owner_user_id="u", animal_id="pet", deleted_at=None,
                             measured_at=datetime(2026, 8, 25, tzinfo=UTC), normalized_value="10")
    phase6.measurements = {"m1": first, "m2": second}
    stable_service = WeeklyReportService(pets, phase6)
    assert stable_service.generate("u", "pet", datetime(2026, 8, 26, tzinfo=UTC)).change_state == "NO_MEANINGFUL_CHANGE"
    second.normalized_value = "11"
    changing_service = WeeklyReportService(pets, phase6)
    assert changing_service.generate("u", "pet", datetime(2026, 8, 26, tzinfo=UTC)).change_state == "MEANINGFUL_CHANGE"


def test_report_claims_keep_source_references_and_get_does_not_regenerate():
    pet = SimpleNamespace(id="pet")
    phase6 = SimpleNamespace(
        timeline=lambda owner, pet_id, limit=100: [{
            "source_entity_type": "PETI_CHECK", "source_entity_id": "check-1", "status": "CLEAR",
        }],
        measurements={},
    )
    pets = SimpleNamespace(get=lambda owner, pet_id: pet)
    service = WeeklyReportService(pets, phase6)
    report = service.generate("u", "pet", datetime(2026, 8, 26, tzinfo=UTC))
    assert report.source_references
    assert WeeklyReportService.validate(report)["material_claim_source_traceability"]
    phase6.timeline = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("get regenerated report"))
    assert service.get("u", report.id) is report


def test_concurrent_weekly_report_generation_is_singleton_per_week():
    pet = SimpleNamespace(id="pet")
    phase6 = SimpleNamespace(timeline=lambda owner, pet_id, limit=100: [], measurements={})
    pets = SimpleNamespace(get=lambda owner, pet_id: pet)
    service = WeeklyReportService(pets, phase6)
    at = datetime(2026, 8, 26, tzinfo=UTC)
    with ThreadPoolExecutor(max_workers=10) as pool:
        reports = list(pool.map(lambda _: service.generate("u", "pet", at), range(10)))
    assert len({report.id for report in reports}) == 1
    assert len(service.reports) == 1


def test_weekly_report_read_is_owner_scoped():
    pet = SimpleNamespace(id="pet")
    phase6 = SimpleNamespace(timeline=lambda owner, pet_id, limit=100: [], measurements={})
    pets = SimpleNamespace(get=lambda owner, pet_id: pet)
    service = WeeklyReportService(pets, phase6)
    report = service.generate("owner-a", "pet", datetime(2026, 8, 26, tzinfo=UTC))
    with pytest.raises(ValueError, match="REPORT_NOT_FOUND"):
        service.get("owner-b", report.id)
