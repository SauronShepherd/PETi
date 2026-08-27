from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import pytest
from app.collaboration.service import CollaborationService, PetAuthorizationService


class FakePets:
    def get(self, owner: str, pet_id: str):
        return {"owner": owner, "id": pet_id} if owner == "owner-1" else None


class MemoryStore:
    def __init__(self):
        self.rows: dict[str, dict] = {}

    def all(self, collection: str):
        return list(self.rows.values()) if collection == "collaboration_memberships" else []

    def put(self, collection: str, item):
        self.rows[item.id] = asdict(item)


def test_membership_hydrates_after_restart_and_revocation_persists():
    store = MemoryStore()
    first = CollaborationService(FakePets(), store=store)
    membership = first.grant("owner-1", "pet-1", "caregiver-1")

    restarted = CollaborationService(FakePets(), store=store)
    assert restarted.authorize("caregiver-1", "pet-1", "READ_SHARED_HISTORY").id == membership.id
    restarted.revoke("owner-1", membership.id)

    restarted_again = CollaborationService(FakePets(), store=store)
    with pytest.raises(ValueError, match="COLLABORATION_FORBIDDEN"):
        restarted_again.authorize("caregiver-1", "pet-1", "READ_SHARED_HISTORY")


def test_pet_authorization_prefers_owner_and_keeps_membership_pet_scoped():
    service = CollaborationService(FakePets())
    service.grant("owner-1", "pet-1", "caregiver-1", role="VIEWER")
    authorization = PetAuthorizationService(FakePets(), service)

    assert authorization.require("owner-1", "pet-1")["role"] == "OWNER"
    with pytest.raises(ValueError, match="COLLABORATION_FORBIDDEN"):
        authorization.require("caregiver-1", "pet-2", "READ_SHARED_HISTORY")


def test_membership_expiry_uses_injectable_clock():
    now = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
    service = CollaborationService(FakePets(), clock=lambda: now)
    membership = service.grant("owner-1", "pet-1", "caregiver-1", ttl_hours=1)
    assert service.authorize("caregiver-1", "pet-1", "READ_SHARED_HISTORY").id == membership.id

    expired = CollaborationService(FakePets(), clock=lambda: now + timedelta(hours=1))
    expired.memberships[membership.id] = membership
    with pytest.raises(ValueError, match="COLLABORATION_FORBIDDEN"):
        expired.authorize("caregiver-1", "pet-1", "READ_SHARED_HISTORY")


def test_membership_rejects_malformed_ttl():
    service = CollaborationService(FakePets())
    with pytest.raises(ValueError, match="MEMBERSHIP_TTL_INVALID"):
        service.grant("owner-1", "pet-1", "caregiver-1", ttl_hours="one")
