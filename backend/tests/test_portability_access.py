import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from app.api.v1 import create_portable_share
from app.portability.service import PortabilityService


def test_share_resolution_requires_digest_match_and_rejects_revoked_grants():
    service = PortabilityService(lambda owner, pet_id: {})
    share = service.create_share("owner-1", "pet-1")
    grant = service.resolve_share(share["share_id"], share["token"])
    assert grant.pet_id == "pet-1"
    with pytest.raises(ValueError, match="SHARE_NOT_FOUND"):
        service.resolve_share(share["share_id"], "wrong-token")
    service.revoke("owner-1", share["share_id"])
    with pytest.raises(ValueError, match="SHARE_NOT_FOUND"):
        service.resolve_share(share["share_id"], share["token"])


def test_revoke_response_redacts_token_digest():
    service = PortabilityService(lambda owner, pet_id: {})
    share = service.create_share("owner-1", "pet-1")
    revoked = service.revoke("owner-1", share["share_id"])
    assert "token_digest" not in revoked


def test_portable_share_api_rejects_malformed_ttl_as_client_error():
    service = PortabilityService(lambda owner, pet_id: {})
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(
        portability=service, pets=SimpleNamespace(get=lambda owner, pet_id: object())
    )))
    principal = SimpleNamespace(user_id="owner-1")

    with pytest.raises(Exception) as raised:
        asyncio.run(create_portable_share("pet-1", {"ttl_hours": "not-a-number"}, request, principal))

    assert raised.value.status_code == 400
    assert raised.value.detail == "SHARE_POLICY_INVALID"


@pytest.mark.parametrize("ttl", [True, 24.5, "24"])
def test_portable_share_api_does_not_coerce_non_integer_ttl(ttl):
    service = PortabilityService(lambda owner, pet_id: {})
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(
        portability=service, pets=SimpleNamespace(get=lambda owner, pet_id: object())
    )))
    principal = SimpleNamespace(user_id="owner-1")

    with pytest.raises(Exception) as raised:
        asyncio.run(create_portable_share("pet-1", {"ttl_hours": ttl}, request, principal))

    assert raised.value.status_code == 400
    assert raised.value.detail == "SHARE_POLICY_INVALID"


def test_portable_export_rejects_non_boolean_raw_media_flag():
    from app.api.v1 import portable_export

    service = PortabilityService(lambda owner, pet_id: {})
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(portability=service)))
    principal = SimpleNamespace(user_id="owner-1")

    with pytest.raises(Exception) as raised:
        asyncio.run(portable_export("pet-1", {"include_raw_media": "false"}, request, principal))

    assert raised.value.status_code == 400
    assert raised.value.detail == "EXPORT_RAW_MEDIA_FLAG_INVALID"


def test_portable_export_maps_missing_pet_to_not_found():
    from app.api.v1 import portable_export

    service = PortabilityService(lambda owner, pet_id: (_ for _ in ()).throw(ValueError("PET_NOT_FOUND")))
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(portability=service)))
    principal = SimpleNamespace(user_id="owner-1")

    with pytest.raises(Exception) as raised:
        asyncio.run(portable_export("missing", {}, request, principal))

    assert raised.value.status_code == 404
    assert raised.value.detail == "PET_NOT_FOUND"


def test_portable_share_rejects_non_owned_pet():
    from app.api.v1 import create_portable_share

    service = PortabilityService(lambda owner, pet_id: {})
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(
        portability=service,
        pets=SimpleNamespace(get=lambda owner, pet_id: None),
    )))
    principal = SimpleNamespace(user_id="owner-1")

    with pytest.raises(Exception) as raised:
        asyncio.run(create_portable_share("other-pet", {}, request, principal))

    assert raised.value.status_code == 404


def test_share_resolution_rejects_expired_grant():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    service = PortabilityService(lambda owner, pet_id: {}, clock=lambda: now)
    share = service.create_share("owner-1", "pet-1", ttl_hours=1)
    expired = PortabilityService(lambda owner, pet_id: {}, clock=lambda: now + timedelta(hours=2))
    expired.shares.update(service.shares)
    with pytest.raises(ValueError, match="SHARE_NOT_FOUND"):
        expired.resolve_share(share["share_id"], share["token"])


@pytest.mark.parametrize("ttl", [True, 24.5, "24"])
def test_portability_service_rejects_coercive_ttl_types(ttl):
    service = PortabilityService(lambda owner, pet_id: {})

    with pytest.raises(ValueError, match="SHARE_POLICY_INVALID"):
        service.create_share("owner-1", "pet-1", ttl_hours=ttl)


@pytest.mark.parametrize("share_id,token", [(None, "token"), ("share", None), ("share", 1)])
def test_share_resolution_rejects_non_string_credentials(share_id, token):
    service = PortabilityService(lambda owner, pet_id: {})

    with pytest.raises(ValueError, match="SHARE_NOT_FOUND"):
        service.resolve_share(share_id, token)
