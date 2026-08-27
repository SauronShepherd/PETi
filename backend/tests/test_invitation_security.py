import asyncio
import hashlib
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.api.v1 import create_automation_rule
from app.future.service import FutureService
from fastapi import HTTPException


class Pets:
    def get(self, owner, pet_id):
        return {"owner": owner, "id": pet_id}


def test_invitation_persists_only_token_digest():
    class Store:
        def __init__(self):
            self.rows = {}

        def put_raw(self, collection, key, data):
            self.rows[key] = data

        def all(self, collection):
            return list(self.rows.values())

    store = Store()
    service = FutureService(Pets(), store=store)
    invitation = service.create_invitation("owner-1", "pet-1", "caregiver@example.test")
    persisted = store.rows[invitation["id"]]
    assert "token_digest" not in invitation["payload"]
    assert persisted["payload"]["token_digest"] == hashlib.sha256(invitation["token"].encode()).hexdigest()
    assert "token" not in persisted["payload"]
    assert service.find_invitation_by_token(invitation["token"]).id == invitation["id"]


def test_expired_invitation_cannot_be_accepted():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    service = FutureService(Pets(), clock=lambda: now)
    invitation = service.create_invitation("owner-1", "pet-1", "caregiver@example.test", ttl_hours=1)
    expired = FutureService(Pets(), clock=lambda: now + timedelta(hours=2))
    expired.items.update(service.items)
    assert expired.find_invitation_by_token(invitation["token"]) is None


def test_invitation_is_consumed_and_cannot_be_replayed():
    service = FutureService(Pets())
    invitation = service.create_invitation("owner-1", "pet-1", "caregiver@example.test")
    accepted = service.consume_invitation(invitation["token"])
    assert accepted.status == "ACCEPTED"
    assert service.find_invitation_by_token(invitation["token"]) is None


def test_invitation_ttl_rejects_coercive_types():
    service = FutureService(Pets())
    for ttl in (True, 24.5, "24"):
        try:
            service.create_invitation("owner-1", "pet-1", "caregiver-user", ttl_hours=ttl)
        except ValueError as exc:
            assert str(exc) == "INVITATION_TTL_INVALID"
        else:
            raise AssertionError("invalid invitation TTL must be rejected")


def test_invitation_rejects_wrong_authenticated_invitee():
    service = FutureService(Pets())
    invitation = service.create_invitation("owner-1", "pet-1", "caregiver-user")

    try:
        service.consume_invitation(invitation["token"], expected_invitee="other-user")
    except ValueError as exc:
        assert str(exc) == "INVITATION_INVITEE_MISMATCH"
    else:
        raise AssertionError("wrong invitee must be rejected")

    assert service.find_invitation_by_token(invitation["token"]) is not None


def test_invitation_token_lookup_rejects_non_string_credentials():
    service = FutureService(Pets())

    assert service.find_invitation_by_token(None) is None
    try:
        service.consume_invitation(123)
    except ValueError as exc:
        assert str(exc) == "INVITATION_NOT_FOUND_OR_EXPIRED"
    else:
        raise AssertionError("non-string invitation token must be rejected")


def test_automation_enabled_flag_does_not_truthy_coerce_strings():
    service = FutureService(Pets())
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(future=service)))
    principal = SimpleNamespace(user_id="owner-1")

    try:
        asyncio.run(create_automation_rule("pet-1", {"enabled": "false"}, request, principal))
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "AUTOMATION_ENABLED_FLAG_INVALID"
    else:
        raise AssertionError("string automation flags must be rejected")
