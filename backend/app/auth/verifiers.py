from typing import Protocol

from .models import AuthFailure, ExternalIdentity


class IdentityVerifier(Protocol):
    async def verify_bearer_token(self, token: str) -> ExternalIdentity: ...


class LocalTestIdentityVerifier:
    """Accepts only LOCAL_TEST tokens; never enabled outside LOCAL."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    async def verify_bearer_token(self, token: str) -> ExternalIdentity:
        if not self.enabled or not isinstance(token, str):
            raise ValueError(AuthFailure.INVALID.value)
        if not token.startswith("local-test:"):
            raise ValueError(AuthFailure.INVALID.value)
        uid = token.removeprefix("local-test:").strip()
        if not uid or len(uid) > 128 or any(
            ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
            for ch in uid
        ):
            raise ValueError(AuthFailure.INVALID.value)
        return ExternalIdentity(uid)


class FirebaseIdentityVerifier:
    def __init__(self, firebase_auth: object):
        self.firebase_auth = firebase_auth

    async def verify_bearer_token(self, token: str) -> ExternalIdentity:
        try:
            if not isinstance(token, str) or not token.strip():
                raise ValueError
            decoded = self.firebase_auth.verify_id_token(token)  # type: ignore[attr-defined]
            uid = decoded.get("uid") or decoded.get("sub")
            if not isinstance(uid, str) or not uid.strip() or len(uid) > 128:
                raise ValueError
            return ExternalIdentity(uid)
        except Exception as exc:
            raise ValueError(AuthFailure.INVALID.value) from exc
