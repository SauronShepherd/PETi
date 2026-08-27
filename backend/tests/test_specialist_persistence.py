from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier
from types import SimpleNamespace

from app.specialists.service import SpecialistService, SpecialistStatus


class Store:
    def __init__(self, rows):
        self.rows = rows

    def all(self, collection):
        assert collection in {"specialist_analyses", "initial_scan_candidates", "initial_scan_candidate_reviews"}
        return list(self.rows)

    def put_raw(self, collection, key, data):
        assert collection == "specialist_analyses"
        self.rows[:] = [row for row in self.rows if row.get("id") != key]
        self.rows.append(dict(data))


class Pets:
    def get(self, owner, pet_id):
        return SimpleNamespace(id=pet_id, species="DOG") if owner == "owner-1" else None


class Media:
    def get_owned(self, owner, media_id):
        return SimpleNamespace(status="READY", media_type="IMAGE")


class Credits:
    def __init__(self):
        self.consume_calls = 0

    def consume(self, reservation_id, operation_id):
        self.consume_calls += 1


def test_specialist_service_hydrates_queued_analysis_after_restart():
    now = datetime.now(UTC)
    row = {
        "id": "analysis-1",
        "owner_user_id": "owner-1",
        "animal_id": "pet-1",
        "analysis_type": "DOG_DENTAL_CHECK",
        "media_asset_ids": ["image-1"],
        "status": "QUEUED",
        "result": {},
        "provenance": {"capture_manifest": {"steps": []}, "owner_context": {"comfort": "okay"}},
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "deleted_at": None,
    }

    service = SpecialistService(Pets(), Media(), store=Store([row]))

    analysis = service._owned("owner-1", "analysis-1")
    assert analysis.status == SpecialistStatus.QUEUED
    assert service.pending_requests["analysis-1"] == {
        "media_asset_ids": ["image-1"],
        "capture_manifest": {"steps": []},
        "owner_context": {"comfort": "okay"},
    }
    completed = service.complete_task("owner-1", "analysis-1", {}, "GEMINI", "gemini-3.5-flash")
    assert completed.provenance["provider"] == "GEMINI"
    assert completed.provenance["provider_model"] == "gemini-3.5-flash"


def test_specialist_duplicate_delivery_consumes_funding_once():
    now = datetime.now(UTC)
    row = {
        "id": "analysis-duplicate",
        "owner_user_id": "owner-1",
        "animal_id": "pet-1",
        "analysis_type": "DOG_DENTAL_CHECK",
        "media_asset_ids": [],
        "status": "QUEUED",
        "result": {},
        "provenance": {"funding_reservation_id": "reservation-1"},
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "deleted_at": None,
    }
    credits = Credits()
    service = SpecialistService(Pets(), Media(), store=Store([row]), credits=credits)
    barrier = Barrier(2)

    def complete():
        barrier.wait()
        return service.complete_task("owner-1", "analysis-duplicate", {})

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: complete(), range(2)))

    assert all(item.status == SpecialistStatus.COMPLETED for item in results)
    assert credits.consume_calls == 1


def test_specialist_service_hydrates_initial_scan_candidates_and_reviews():
    now = datetime(2026, 8, 26, tzinfo=UTC)

    class MultiStore(Store):
        def __init__(self):
            self.collections = {
                "specialist_analyses": [],
                "initial_scan_candidates": [{
                    "id": "candidate-1", "analysis_id": "analysis-1", "owner_user_id": "owner-1",
                    "animal_id": "pet-1", "field_type": "COAT_COLOR", "candidate_value": "black",
                    "created_at": now.isoformat(), "reviewed_at": None,
                }],
                "initial_scan_candidate_reviews": [{
                    "id": "review-1", "candidate_id": "candidate-1", "owner_user_id": "owner-1",
                    "action": "CONFIRM", "value": "black", "created_at": now.isoformat(),
                }],
            }

        def all(self, collection):
            return list(self.collections.get(collection, []))

    service = SpecialistService(Pets(), Media(), store=MultiStore())
    assert service.candidates["candidate-1"].created_at == now
    assert service.candidate_reviews[0].id == "review-1"
