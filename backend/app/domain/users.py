from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "CUSTOMER"
    INTERNAL_TEST = "INTERNAL_TEST"
    ADMIN = "ADMIN"


@dataclass
class User:
    id: str
    firebase_uid: str
    role: UserRole = UserRole.CUSTOMER
    billing_exempt: bool = False
    ads_exempt: bool = False
    internal_persona_code: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
