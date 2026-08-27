import hashlib

from app.portability.service import PortabilityService


def test_share_returns_raw_token_once_but_stores_only_digest():
    service = PortabilityService(lambda owner, pet_id: {})
    response = service.create_share("owner-1", "pet-1")
    grant = service.shares[response["share_id"]]

    assert response["token"]
    assert grant.token_digest == hashlib.sha256(response["token"].encode()).hexdigest()
    assert grant.token_digest != response["token"]
