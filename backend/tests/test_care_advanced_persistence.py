from dataclasses import asdict
from datetime import UTC, datetime

import pytest
from app.care_advanced.domain import CareRecordsService


class FakePets:
    def get(self, owner: str, pet_id: str):
        return {"owner": owner, "id": pet_id}


class StrictFakePets(FakePets):
    def get(self, owner: str, pet_id: str):
        return super().get(owner, pet_id) if pet_id == "pet-1" else None


class MemoryStore:
    def __init__(self):
        self.rows: dict[str, dict] = {}

    def all(self, collection: str):
        return list(self.rows.values()) if collection == "care_records" else []

    def list_owned(self, collection: str, owner: str):
        return [row for row in self.all(collection) if row.get("owner_user_id") == owner]

    def put(self, collection: str, record):
        self.rows[record.id] = asdict(record)


def test_care_records_hydrate_after_restart_and_persist_soft_delete():
    store = MemoryStore()
    first = CareRecordsService(FakePets(), store=store)
    record = first.create("owner-1", "pet-1", "VACCINATION", {"name": "Rabies"})

    restarted = CareRecordsService(FakePets(), store=store)
    assert [item.id for item in restarted.list("owner-1", "pet-1")] == [record.id]
    restarted.delete("owner-1", record.id)

    restarted_again = CareRecordsService(FakePets(), store=store)
    assert restarted_again.list("owner-1", "pet-1") == []
    assert restarted_again.records[record.id].status == "DELETED"


def test_care_records_hydration_preserves_owner_boundaries():
    store = MemoryStore()
    service = CareRecordsService(FakePets(), store=store)
    service.create("owner-1", "pet-1", "JOURNAL", {"text": "walk"})
    service.create("owner-2", "pet-1", "JOURNAL", {"text": "walk"})

    restarted = CareRecordsService(FakePets(), store=store)
    assert len(restarted.list("owner-1", "pet-1")) == 1
    assert len(restarted.list("owner-2", "pet-1")) == 1


def test_care_record_update_is_owner_scoped_and_rejects_clinical_advice():
    service = CareRecordsService(FakePets())
    record = service.create("owner-1", "pet-1", "MEDICATION", {"name": "Documented item"})
    updated = service.update("owner-1", record.id, {"name": "Updated documented item"})
    assert updated.payload["name"] == "Updated documented item"
    with pytest.raises(ValueError, match="CARE_RECORD_NOT_FOUND"):
        service.update("owner-2", record.id, {"name": "not allowed"})
    with pytest.raises(ValueError, match="MEDICATION_CLINICAL_ADVICE_NOT_ALLOWED"):
        service.update("owner-1", record.id, {"prescription": "take this"})


def test_care_record_reads_validate_pet_ownership_and_payload_shape():
    service = CareRecordsService(StrictFakePets())
    with pytest.raises(ValueError, match="CARE_RECORD_PAYLOAD_INVALID"):
        service.create("owner-1", "pet-1", "JOURNAL", "not-a-dict")
    assert service.list("owner-2", "pet-1") == []
    with pytest.raises(ValueError, match="PET_NOT_FOUND"):
        service.longitudinal_bundle("owner-1", "pet-2")


def test_care_record_mutations_use_injected_clock():
    instant = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
    service = CareRecordsService(FakePets(), clock=lambda: instant)
    record = service.create("owner-1", "pet-1", "JOURNAL", {"text": "walk"})
    service.update("owner-1", record.id, {"text": "long walk"})
    assert record.updated_at == instant
    service.delete("owner-1", record.id)
    assert record.deleted_at == instant
