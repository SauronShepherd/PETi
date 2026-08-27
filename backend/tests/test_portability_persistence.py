from dataclasses import asdict

import pytest
from app.portability.service import PortabilityService


class MemoryStore:
    def __init__(self):
        self.rows: dict[str, dict] = {}

    def all(self, collection: str):
        return list(self.rows.values()) if collection == "portability_share_grants" else []

    def put(self, collection: str, grant):
        self.rows[grant.id] = asdict(grant)


def test_share_grants_hydrate_and_revocation_survives_restart():
    store = MemoryStore()
    first = PortabilityService(lambda owner, pet_id: {}, store=store)
    share = first.create_share("owner-1", "pet-1")
    first.revoke("owner-1", share["share_id"])

    restarted = PortabilityService(lambda owner, pet_id: {}, store=store)
    assert restarted.shares[share["share_id"]].revoked_at is not None
    with pytest.raises(ValueError, match="SHARE_NOT_FOUND"):
        restarted.revoke("other-owner", share["share_id"])
