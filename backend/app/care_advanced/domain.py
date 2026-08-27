from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any, ClassVar
from uuid import uuid4


@dataclass
class CareRecord:
    owner_user_id: str
    pet_id: str
    record_type: str
    payload: dict
    id: str = field(default_factory=lambda: str(uuid4()))
    source: str = "OWNER_ENTERED"
    status: str = "ACTIVE"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None


class CareRecordsService:
    ALLOWED: ClassVar[set[str]] = {"CARE_PLAN", "VACCINATION", "MEDICATION", "MEDICATION_SCHEDULE", "MEDICATION_OCCURRENCE", "APPOINTMENT", "FOLLOW_UP", "JOURNAL", "VISIT_PREPARATION", "LONGITUDINAL_BUNDLE"}

    def __init__(self, pets, store: Any | None = None, clock=None):
        self.pets = pets
        self.store = store
        self.clock = clock or (lambda: datetime.now(UTC))
        self.records: dict[str, CareRecord] = {}
        self.lock = RLock()
        self._hydrate()

    def _hydrate(self) -> None:
        """Reload active and deleted records after a process restart."""
        if not self.store or not hasattr(self.store, "list_owned"):
            return
        try:
            rows = self.store.all("care_records") if hasattr(self.store, "all") else []
        except Exception:  # noqa: BLE001 - startup must remain fail-closed on bad rows
            rows = []
        for row in rows:
            try:
                data = dict(row)
                for key in ("created_at", "updated_at", "deleted_at"):
                    value = data.get(key)
                    if value is not None and not isinstance(value, datetime):
                        data[key] = datetime.fromisoformat(str(value))
                record = CareRecord(
                    **{key: data[key] for key in CareRecord.__dataclass_fields__ if key in data}
                )
                self.records[record.id] = record
            except (KeyError, TypeError, ValueError):
                continue

    def create(self, owner: str, pet_id: str, record_type: str, payload: dict, source: str = "OWNER_ENTERED") -> CareRecord:
        with self.lock:
            if not self.pets.get(owner, pet_id): raise ValueError("PET_NOT_FOUND")
            if record_type not in self.ALLOWED: raise ValueError("CARE_RECORD_TYPE_NOT_SUPPORTED")
            self._validate_payload(record_type, payload)
            value = CareRecord(owner, pet_id, record_type, dict(payload), source=source)
            self.records[value.id] = value
            if self.store and hasattr(self.store, "put"):
                self.store.put("care_records", value)
            return value

    @staticmethod
    def _validate_payload(record_type: str, payload: dict) -> None:
        if not isinstance(payload, dict):
            raise ValueError("CARE_RECORD_PAYLOAD_INVALID")  # noqa: TRY004 - public domain error contract
        if record_type == "MEDICATION" and any(
            key in payload for key in ("recommendation", "prescription", "diagnosis")
        ):
            raise ValueError("MEDICATION_CLINICAL_ADVICE_NOT_ALLOWED")

    def update(self, owner: str, record_id: str, payload: dict) -> CareRecord:
        with self.lock:
            value = self.records.get(record_id)
            if not value or value.owner_user_id != owner or value.deleted_at:
                raise ValueError("CARE_RECORD_NOT_FOUND")
            self._validate_payload(value.record_type, payload)
            value.payload = dict(payload)
            value.updated_at = self.clock()
            if self.store and hasattr(self.store, "put"):
                self.store.put("care_records", value)
            return value

    def list(self, owner: str, pet_id: str, record_type: str | None = None):
        with self.lock:
            return [x for x in self.records.values() if x.owner_user_id == owner and x.pet_id == pet_id and not x.deleted_at and (record_type is None or x.record_type == record_type)]

    def delete(self, owner: str, record_id: str):
        with self.lock:
            value = self.records.get(record_id)
            if not value or value.owner_user_id != owner: raise ValueError("CARE_RECORD_NOT_FOUND")
            value.deleted_at = self.clock()
            value.updated_at = value.deleted_at
            value.status = "DELETED"
            if self.store and hasattr(self.store, "put"):
                self.store.put("care_records", value)
            return value

    def longitudinal_bundle(self, owner: str, pet_id: str) -> dict:
        if not self.pets.get(owner, pet_id):
            raise ValueError("PET_NOT_FOUND")
        rows = self.list(owner, pet_id)
        return {"pet_id": pet_id, "bundle_version": "1.0.0", "items": [asdict(x) for x in rows], "summary_type": "DETERMINISTIC_CHANGE_SUMMARY"}
