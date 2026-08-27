"""Safe, deterministic foundations for Phases 21–26."""
import hashlib
import secrets
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from threading import RLock
from uuid import uuid4


class FutureDomainError(ValueError):
    pass


@dataclass
class FutureItem:
    id: str
    owner_user_id: str
    pet_id: str | None = None
    kind: str = ""
    status: str = "ACTIVE"
    payload: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None


class FutureService:
    def __init__(self, pets, phase6=None, records=None, reports=None, store=None, clock=None):
        self.pets, self.phase6, self.records, self.reports, self.store = pets, phase6, records, reports, store
        self.clock = clock or (lambda: datetime.now(UTC)); self.items: dict[str, FutureItem] = {}; self.tokens: dict[str, str] = {}; self.lock = RLock()
        self._hydrate()

    def _hydrate(self):
        if not self.store or not hasattr(self.store, "all"):
            return
        try:
            rows = self.store.all("future_domain_items")
        except Exception:  # noqa: BLE001 - unavailable durable state must not crash startup
            rows = []
        for raw in rows:
            try:
                data = dict(raw)
                for key in ("created_at", "updated_at", "deleted_at"):
                    value = data.get(key)
                    if value is not None and not isinstance(value, datetime):
                        data[key] = datetime.fromisoformat(str(value))
                item = FutureItem(**{key: data[key] for key in FutureItem.__dataclass_fields__ if key in data})
                self.items[item.id] = item
            except (KeyError, TypeError, ValueError):
                continue

    def _save(self, item):
        if self.store and hasattr(self.store, "put_raw"): self.store.put_raw("future_domain_items", item.id, asdict(item))

    def _pet(self, owner, pet_id):
        if not self.pets.get(owner, pet_id): raise FutureDomainError("PET_NOT_FOUND")

    def assert_pet(self, owner, pet_id):
        with self.lock:
            self._pet(owner, pet_id)

    def create(self, owner, kind, pet_id=None, payload=None):
        with self.lock:
            if pet_id: self._pet(owner, pet_id)
            now = self.clock(); item = FutureItem(str(uuid4()), owner, pet_id, kind, payload=payload or {}, created_at=now, updated_at=now); self.items[item.id] = item; self._save(item); return item

    def create_invitation(self, owner, pet_id, invitee, role="CAREGIVER", ttl_hours=72):
        if not isinstance(invitee, str) or not invitee.strip():
            raise FutureDomainError("INVITATION_INVITEE_REQUIRED")
        if role not in {"CAREGIVER", "VIEWER"}:
            raise FutureDomainError("INVITATION_ROLE_INVALID")
        if isinstance(ttl_hours, bool) or not isinstance(ttl_hours, int) or not 1 <= ttl_hours <= 168:
            raise FutureDomainError("INVITATION_TTL_INVALID")
        raw_token = secrets.token_urlsafe(32)
        expires_at = self.clock() + __import__("datetime").timedelta(hours=ttl_hours)
        item = self.create(
            owner,
            "INVITATION",
            pet_id,
            {"invitee": invitee, "role": role, "expires_at": expires_at.isoformat(),
             "token_digest": hashlib.sha256(raw_token.encode()).hexdigest()},
        )
        response = self.public(item)
        response["payload"].pop("token_digest", None)
        response["token"] = raw_token
        return response

    def find_invitation_by_token(self, token):
        with self.lock:
            return self._find_invitation_by_token(token)

    def _find_invitation_by_token(self, token):
        if not isinstance(token, str):
            return None
        digest = hashlib.sha256(token.encode()).hexdigest()
        return next(
            (item for item in self.items.values()
             if item.kind == "INVITATION" and item.payload.get("token_digest") == digest
             and item.status == "ACTIVE" and not item.deleted_at and self._not_expired(item)),
            None,
        )

    def consume_invitation(self, token, expected_invitee=None):
        with self.lock:
            return self._consume_invitation(token, expected_invitee)

    def _consume_invitation(self, token, expected_invitee=None):
        item = self.find_invitation_by_token(token)
        if not item:
            raise FutureDomainError("INVITATION_NOT_FOUND_OR_EXPIRED")
        if expected_invitee is not None and item.payload.get("invitee") != expected_invitee:
            raise FutureDomainError("INVITATION_INVITEE_MISMATCH")
        item.status = "ACCEPTED"
        item.updated_at = self.clock()
        self._save(item)
        return item

    def _not_expired(self, item):
        value = item.payload.get("expires_at")
        if not value:
            return False
        try:
            return datetime.fromisoformat(str(value)) > self.clock()
        except ValueError:
            return False

    def owned(self, owner, item_id, kind=None):
        with self.lock:
            item = self.items.get(item_id)
            if not item or item.owner_user_id != owner or item.deleted_at or (kind and item.kind != kind): raise FutureDomainError("FUTURE_ITEM_NOT_FOUND")
            return item

    def list(self, owner, kind, pet_id=None):
        with self.lock:
            return [x for x in self.items.values() if x.owner_user_id == owner and x.kind == kind and not x.deleted_at and (pet_id is None or x.pet_id == pet_id)]

    def owner_items(self, owner, include_deleted=False):
        with self.lock:
            return [x for x in self.items.values() if x.owner_user_id == owner and (include_deleted or not x.deleted_at)]

    def delete_owner(self, owner, now=None):
        with self.lock:
            deleted = []
            timestamp = now or self.clock()
            for item in self.items.values():
                if item.owner_user_id == owner and not item.deleted_at:
                    item.deleted_at = timestamp; item.updated_at = timestamp; item.status = "DELETED"
                    self._save(item)
                    deleted.append(item)
            return deleted

    def delete(self, owner, item_id, kind=None):
        with self.lock:
            item = self.owned(owner, item_id, kind)
            item.deleted_at = self.clock(); item.status = "DELETED"; item.updated_at = item.deleted_at; self._save(item); return item

    def update(self, owner, item_id, kind, changes):
        """Atomically apply an allowlisted payload update to an owned item."""
        with self.lock:
            item = self.owned(owner, item_id, kind)
            item.payload.update(changes)
            item.updated_at = self.clock()
            self._save(item)
            return item

    def transition(self, owner, item_id, kind, status):
        """Atomically transition an owned workflow item and persist it."""
        with self.lock:
            item = self.owned(owner, item_id, kind)
            item.status = status
            item.updated_at = self.clock()
            self._save(item)
            return item

    def export(self, owner, pet_id):
        self._pet(owner, pet_id)
        return self.create(owner, "EXPORT", pet_id, {"export_version": "1.0.0", "status": "READY", "source_scope": "PET_OWNER_SCOPED", "includes_billing": False, "raw_media": False})

    def share(self, owner, export_id, payload):
        export = self.owned(owner, export_id, "EXPORT")
        scope = payload.get("scope", "READ_ONLY")
        if scope not in {"READ_ONLY", "VISIT_PACKET"}: raise FutureDomainError("SHARE_SCOPE_INVALID")
        raw_token = secrets.token_urlsafe(32)
        item = self.create(owner, "SHARE", export.pet_id, {"export_id": export.id, "expires_at": payload.get("expires_at"), "scope": scope, "token_digest": hashlib.sha256(raw_token.encode()).hexdigest()})
        response = self.public(item)
        response["payload"].pop("token_digest", None)
        response["token"] = raw_token
        return response

    def import_item(self, owner, payload):
        if payload.get("manifest", {}).get("schema") not in {None, "PETI_PORTABLE_PACKAGE"}:
            raise FutureDomainError("IMPORT_SCHEMA_UNSUPPORTED")
        return self.create(owner, "IMPORT", payload=payload | {"status": "PREVIEW_REQUIRED", "duplicate_policy": "PRESERVE_AND_LINK"})

    def search(self, owner, query, pet_id=None):
        with self.lock:
            if pet_id: self._pet(owner, pet_id)
            query = query.strip().lower()[:200]; results = []
            if self.records:
                for doc in self.records.documents.values():
                    if doc.owner_user_id == owner and not doc.deleted_at and (pet_id is None or doc.animal_id == pet_id) and query in (doc.title + " " + (doc.provider_name or "")).lower(): results.append({"type": "RECORD", "id": doc.id, "pet_id": doc.animal_id, "title": doc.title})
            if self.phase6:
                for m in self.phase6.measurements.values():
                    if m.owner_user_id == owner and not m.deleted_at and (pet_id is None or m.animal_id == pet_id) and query in (m.original_value + " " + m.original_unit + " " + m.measurement_type).lower(): results.append({"type": "MEASUREMENT", "id": m.id, "pet_id": m.animal_id, "title": m.measurement_type})
            return results[:100]

    def assistant_message(self, owner, thread_id, message):
        with self.lock:
            thread = self.owned(owner, thread_id, "ASSISTANT_THREAD")
            query = str(message.get("text", "")); sources = self.search(owner, query, thread.pet_id)
            medical = any(word in query.lower() for word in ("diagnose", "disease", "prescribe", "dose", "emergency"))
            response = {"schema_version": "1.0.0", "text": "I can summarize recorded PETi history, but I cannot diagnose, prescribe, or infer facts not present in your records." if medical else ("I found matching PETi sources. Review the cited records for the canonical details." if sources else "I could not find a matching PETi source, so I cannot provide a factual history answer."), "source_references": sources, "grounding_status": "SAFETY_REDIRECT" if medical else ("GROUNDED" if sources else "NO_MATCHING_SOURCE")}
            thread.payload.setdefault("messages", []).extend([{"role": "user", "text": query}, {"role": "assistant", **response}]); thread.updated_at = self.clock(); self._save(thread); return response

    @staticmethod
    def public(value):
        result = asdict(value)
        payload = result.get("payload")
        if isinstance(payload, dict):
            payload.pop("token_digest", None)
            payload.pop("token", None)
        return result
