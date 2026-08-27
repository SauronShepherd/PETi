from datetime import UTC, datetime

from app.search.memory import MemoryService


class MemoryStore:
    def __init__(self):
        self.rows: dict[str, dict] = {}

    def all(self, collection: str):
        return list(self.rows.values()) if collection == "personal_pet_memories" else []

    def put_raw(self, collection: str, key: str, data: dict):
        self.rows[key] = data

    def delete(self, collection: str, key: str):
        self.rows.pop(key, None)


def test_personal_memory_hydrates_and_source_invalidation_is_durable():
    store = MemoryStore()
    first = MemoryService(store=store)
    item = first.refresh("owner-1", "pet-1", "PREFERENCES", {"color": "blue"}, ["source-1"])

    restarted = MemoryService(store=store)
    assert restarted.memories[("owner-1", "pet-1", "PREFERENCES")].payload == {"color": "blue"}
    assert [item.animal_id for item in restarted.list("owner-1", "pet-1")] == ["pet-1"]
    assert restarted.list("owner-2", "pet-1") == []
    restarted.invalidate_source("source-1")

    reloaded = MemoryService(store=store)
    restored = reloaded.memories[("owner-1", "pet-1", "PREFERENCES")]
    assert restored.source_ids == []
    assert restored.version == item.version + 1


def test_personal_memory_hydrates_firestore_iso_timestamp_and_uses_clock():
    store = MemoryStore()
    fixed = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
    first = MemoryService(store=store, clock=lambda: fixed)
    first.refresh("owner-1", "pet-1", "PREFERENCES", {"color": "blue"}, [])

    store.rows["owner-1:pet-1:PREFERENCES"]["refreshed_at"] = fixed.isoformat()
    restarted = MemoryService(store=store, clock=lambda: fixed)

    assert restarted.memories[("owner-1", "pet-1", "PREFERENCES")].refreshed_at == fixed


def test_personal_memory_owner_deletion_removes_durable_rows():
    store = MemoryStore()
    service = MemoryService(store=store)
    service.refresh("owner-1", "pet-1", "PREFERENCES", {"color": "blue"}, [])
    service.refresh("owner-2", "pet-2", "PREFERENCES", {"color": "red"}, [])

    assert service.delete_owner("owner-1") == 1
    assert service.memories.keys() == {("owner-2", "pet-2", "PREFERENCES")}
    assert list(store.rows) == ["owner-2:pet-2:PREFERENCES"]
