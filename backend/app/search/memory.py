from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any


@dataclass
class PersonalPetMemory:
    owner_user_id: str
    animal_id: str
    memory_type: str
    payload: dict
    source_ids: list[str] = field(default_factory=list)
    version: int = 1
    refreshed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class MemoryService:
    def __init__(self, store: Any | None = None, clock=None):
        self.store = store
        self.clock = clock or (lambda: datetime.now(UTC))
        self.memories: dict[tuple[str, str, str], PersonalPetMemory] = {}
        self.lock = RLock()
        self._hydrate()

    def _hydrate(self) -> None:
        if not self.store or not hasattr(self.store, "all"):
            return
        try:
            rows = self.store.all("personal_pet_memories")
        except Exception:  # noqa: BLE001 - invalid memory must never become trusted context
            rows = []
        for row in rows:
            try:
                data = dict(row)
                refreshed_at = data.get("refreshed_at")
                if refreshed_at is not None and not isinstance(refreshed_at, datetime):
                    data["refreshed_at"] = datetime.fromisoformat(str(refreshed_at))
                item = PersonalPetMemory(**data)
                self.memories[(item.owner_user_id, item.animal_id, item.memory_type)] = item
            except (KeyError, TypeError, ValueError):
                continue

    def _save(self, item: PersonalPetMemory) -> None:
        if self.store and hasattr(self.store, "put_raw"):
            self.store.put_raw(
                "personal_pet_memories",
                f"{item.owner_user_id}:{item.animal_id}:{item.memory_type}",
                {"owner_user_id": item.owner_user_id, "animal_id": item.animal_id,
                 "memory_type": item.memory_type, "payload": item.payload,
                 "source_ids": item.source_ids, "version": item.version,
                 "refreshed_at": item.refreshed_at},
            )

    def refresh(self, owner, pet_id, memory_type, payload, source_ids):
        with self.lock:
            key = (owner, pet_id, memory_type)
            current = self.memories.get(key)
            value = PersonalPetMemory(owner, pet_id, memory_type, dict(payload), list(source_ids), (current.version + 1 if current else 1), self.clock())
            self.memories[key] = value
            self._save(value)
            return value

    def list(self, owner, pet_id):
        with self.lock:
            return [item for item in self.memories.values() if item.owner_user_id == owner and item.animal_id == pet_id]

    def delete_owner(self, owner):
        with self.lock:
            removed = 0
            for key, item in list(self.memories.items()):
                if item.owner_user_id != owner:
                    continue
                self.memories.pop(key, None)
                removed += 1
                storage_key = f"{item.owner_user_id}:{item.animal_id}:{item.memory_type}"
                if self.store and hasattr(self.store, "delete"):
                    self.store.delete("personal_pet_memories", storage_key)
            return removed

    def invalidate_source(self, source_id):
        with self.lock:
            for value in self.memories.values():
                if source_id in value.source_ids:
                    value.source_ids = [x for x in value.source_ids if x != source_id]
                    value.version += 1
                    value.refreshed_at = self.clock()
                    self._save(value)
