from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock
from typing import Any, ClassVar
from uuid import uuid4


@dataclass
class Membership:
    owner_user_id: str
    member_user_id: str
    pet_id: str
    role: str
    status: str = "ACTIVE"
    expires_at: datetime | None = None
    id: str | None = None


class CollaborationService:
    ROLES: ClassVar[set[str]] = {"CAREGIVER", "VIEWER"}

    def __init__(self, pets, store: Any | None = None, clock=None):
        self.pets, self.store = pets, store
        self.clock = clock or (lambda: datetime.now(UTC))
        self.memberships: dict[str, Membership] = {}
        self.lock = RLock()
        self._hydrate()

    def _hydrate(self) -> None:
        if not self.store or not hasattr(self.store, "all"):
            return
        try:
            rows = self.store.all("collaboration_memberships")
        except Exception:  # noqa: BLE001 - malformed/unavailable rows cannot authorize anyone
            rows = []
        for row in rows:
            try:
                data = dict(row)
                if data.get("expires_at") is not None and not isinstance(data["expires_at"], datetime):
                    data["expires_at"] = datetime.fromisoformat(str(data["expires_at"]))
                item = Membership(**{key: data[key] for key in Membership.__dataclass_fields__ if key in data})
                if item.id:
                    self.memberships[item.id] = item
            except (KeyError, TypeError, ValueError):
                continue

    def grant(self, owner, pet_id, member_user_id, role="CAREGIVER", ttl_hours=None):
        with self.lock:
            return self._grant(owner, pet_id, member_user_id, role, ttl_hours)

    def _grant(self, owner, pet_id, member_user_id, role="CAREGIVER", ttl_hours=None):
        if not self.pets.get(owner, pet_id): raise ValueError("PET_NOT_FOUND")
        if not member_user_id or member_user_id == owner or role not in self.ROLES: raise ValueError("MEMBERSHIP_INVALID")
        if ttl_hours is not None and (isinstance(ttl_hours, bool) or not isinstance(ttl_hours, (int, float)) or ttl_hours <= 0):
            raise ValueError("MEMBERSHIP_TTL_INVALID")
        expiry = self.clock() + timedelta(hours=ttl_hours) if ttl_hours else None
        item = Membership(owner, member_user_id, pet_id, role, expires_at=expiry, id=str(uuid4()))
        self.memberships[item.id] = item
        if self.store and hasattr(self.store, "put"):
            self.store.put("collaboration_memberships", item)
        return item

    def authorize(self, user, pet_id, permission):
        with self.lock:
            for item in self.memberships.values():
                if item.member_user_id == user and item.pet_id == pet_id and item.status == "ACTIVE" and (not item.expires_at or item.expires_at > self.clock()) and (item.role == "CAREGIVER" or permission in {"READ_SHARED_HISTORY", "READ_SHARED_SEARCH"}):
                    return item
        raise ValueError("COLLABORATION_FORBIDDEN")

    def revoke(self, owner, membership_id):
        with self.lock:
            return self._revoke(owner, membership_id)

    def _revoke(self, owner, membership_id):
        item = self.memberships.get(membership_id)
        if not item or item.owner_user_id != owner: raise ValueError("MEMBERSHIP_NOT_FOUND")
        item.status = "REVOKED"
        if self.store and hasattr(self.store, "put"):
            self.store.put("collaboration_memberships", item)
        return asdict(item)


class PetAuthorizationService:
    def __init__(self, pets, collaboration): self.pets, self.collaboration = pets, collaboration
    def require(self, user_id, pet_id, permission="READ"):
        if self.pets.get(user_id, pet_id): return {"role": "OWNER", "permission": permission}
        return {"role": self.collaboration.authorize(user_id, pet_id, permission).role, "permission": permission}
