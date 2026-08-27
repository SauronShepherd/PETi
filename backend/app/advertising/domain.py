from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import uuid4


class RewardIntentStatus(StrEnum):
    CREATED = "CREATED"
    AD_STARTED = "AD_STARTED"
    VERIFIED = "VERIFIED"
    GRANTED = "GRANTED"
    EXPIRED = "EXPIRED"
    CANCELED = "CANCELED"
    INVALID = "INVALID"


@dataclass
class RewardIntent:
    id: str
    user_id: str
    nonce: str
    expected_credit_amount: int
    provider: str
    status: RewardIntentStatus = RewardIntentStatus.CREATED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = field(default_factory=lambda: datetime.now(UTC) + timedelta(minutes=10))
    verified_at: datetime | None = None
    grant_id: str | None = None


def new_intent(user_id: str, amount: int, provider: str, now: datetime | None = None) -> RewardIntent:
    created_at = now or datetime.now(UTC)
    return RewardIntent(
        str(uuid4()), user_id, str(uuid4()), amount, provider,
        created_at=created_at, expires_at=created_at + timedelta(minutes=10),
    )
