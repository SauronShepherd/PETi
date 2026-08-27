from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum


class OperationType(StrEnum):
    PETI_CHECK = "PETI_CHECK"
    AI_PHOTO_STANDARD = "AI_PHOTO_STANDARD"
    AI_VIDEO_STANDARD = "AI_VIDEO_STANDARD"
    AI_AUDIO_STANDARD = "AI_AUDIO_STANDARD"
    AI_DOCUMENT_EXTRACTION = "AI_DOCUMENT_EXTRACTION"
    AI_SPECIALIST_STANDARD = "AI_SPECIALIST_STANDARD"
    AI_PET_HISTORY_QUERY = "AI_PET_HISTORY_QUERY"
    AI_REPORT_NARRATION = "AI_REPORT_NARRATION"
    MEDIA_RETENTION_UNIT = "MEDIA_RETENTION_UNIT"


class FundingSource(StrEnum):
    FREE_ALLOWANCE = "FREE_ALLOWANCE"
    REWARDED_AD = "REWARDED_AD"
    SPONSOR = "SPONSOR"
    PREMIUM = "PREMIUM"
    PROMOTIONAL = "PROMOTIONAL"
    INTERNAL_TEST = "INTERNAL_TEST"
    ADMIN_EXEMPT = "ADMIN_EXEMPT"


class ReservationStatus(StrEnum):
    RESERVED = "RESERVED"
    CONSUMED = "CONSUMED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class LedgerDirection(StrEnum):
    GRANT = "GRANT"
    RESERVE = "RESERVE"
    CONSUME = "CONSUME"
    RELEASE = "RELEASE"
    EXPIRE = "EXPIRE"
    ADJUST = "ADJUST"


@dataclass(frozen=True)
class CostProfile:
    operation_type: OperationType
    version: int
    credit_cost: int
    enabled: bool = True
    effective_from: datetime = field(default_factory=lambda: datetime.now(UTC))
    effective_until: datetime | None = None
    expected_cost_band: str | None = None
    configuration_metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.credit_cost < 0:
            raise ValueError("CREDIT_AMOUNT_MUST_BE_NON_NEGATIVE")


@dataclass
class CreditGrant:
    id: str
    user_id: str
    source: FundingSource
    original_amount: int
    remaining_amount: int
    reserved_amount: int = 0
    expires_at: datetime | None = None
    source_reference: str | None = None
    grant_policy_version: str = "1"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    exhausted_at: datetime | None = None


@dataclass(frozen=True)
class Allocation:
    grant_id: str
    amount: int
    funding_source: FundingSource


@dataclass
class CreditReservation:
    id: str
    user_id: str
    operation_type: OperationType
    cost_profile_version: int
    requested_amount: int
    status: ReservationStatus
    allocation: list[Allocation]
    operation_request_id: str
    idempotency_key: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = field(default_factory=lambda: datetime.now(UTC) + timedelta(minutes=15))
    consumed_at: datetime | None = None
    released_at: datetime | None = None


@dataclass(frozen=True)
class CreditLedgerEntry:
    id: str
    user_id: str
    direction: LedgerDirection
    amount: int
    source: FundingSource | None
    idempotency_key: str
    grant_id: str | None = None
    reservation_id: str | None = None
    operation_request_id: str | None = None
    reason_code: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
