import pytest
from app.auth.task_auth import TaskAuthenticator


def test_bearer_task_auth_uses_verified_service_identity_and_audience():
    def verifier(token, audience):
        assert token == "signed"
        assert audience == "https://worker"
        return {"email": "caller@example.com"}

    auth = TaskAuthenticator(
        "caller@example.com", "https://worker", local=False, token_verifier=verifier
    )
    assert auth.verify_bearer("Bearer signed").service_account == "caller@example.com"


def test_bearer_task_auth_rejects_missing_token():
    with pytest.raises(ValueError, match="AUTHENTICATION_REQUIRED"):
        TaskAuthenticator("caller@example.com", "https://worker", local=False).verify_bearer(None)


def test_bearer_task_auth_rejects_non_string_authorization():
    with pytest.raises(ValueError, match="AUTHENTICATION_REQUIRED"):
        TaskAuthenticator("caller@example.com", "https://worker", local=False).verify_bearer(123)


def test_bearer_task_auth_rejects_empty_bearer_without_verifier_call():
    called = False

    def verifier(_token, _audience):
        nonlocal called
        called = True
        return {"email": "caller@example.com"}

    auth = TaskAuthenticator(
        "caller@example.com", "https://worker", local=False, token_verifier=verifier
    )
    with pytest.raises(ValueError, match="AUTHENTICATION_REQUIRED"):
        auth.verify_bearer("Bearer   ")
    assert called is False


def test_bearer_task_auth_normalizes_verifier_failure():
    def verifier(_token, _audience):
        raise RuntimeError("invalid token")

    auth = TaskAuthenticator(
        "worker@example.com", "https://worker", local=False, token_verifier=verifier
    )
    with pytest.raises(ValueError, match="TASK_SERVICE_IDENTITY_INVALID"):
        auth.verify_bearer("Bearer token")


def test_bearer_task_auth_rejects_non_mapping_claims():
    auth = TaskAuthenticator(
        "worker@example.com",
        "https://worker",
        local=False,
        token_verifier=lambda _token, _audience: ["not", "claims"],
    )
    with pytest.raises(ValueError, match="TASK_SERVICE_IDENTITY_INVALID"):
        auth.verify_bearer("Bearer token")


def test_bearer_task_auth_rejects_whitespace_identity_claim():
    auth = TaskAuthenticator(
        "worker@example.com",
        "https://worker",
        local=False,
        token_verifier=lambda _token, _audience: {"email": "   "},
    )
    with pytest.raises(ValueError, match="TASK_SERVICE_IDENTITY_INVALID"):
        auth.verify_bearer("Bearer token")
