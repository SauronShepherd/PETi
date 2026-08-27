from dataclasses import dataclass
from enum import StrEnum


class AuthFailure(StrEnum):
    MISSING = "AUTH_MISSING_TOKEN"
    INVALID = "AUTH_INVALID_TOKEN"
    EXPIRED = "AUTH_EXPIRED_TOKEN"


@dataclass(frozen=True)
class ExternalIdentity:
    firebase_uid: str


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    firebase_uid: str
    user_id: str
    role: str
    billing_exempt: bool
    ads_exempt: bool
    internal_persona_code: str | None = None
