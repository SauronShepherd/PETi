from dataclasses import dataclass
from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "CUSTOMER"
    INTERNAL_TEST = "INTERNAL_TEST"
    ADMIN = "ADMIN"


class FundingSource(StrEnum):
    FREE_ALLOWANCE = "FREE_ALLOWANCE"
    REWARDED_AD = "REWARDED_AD"
    SPONSOR = "SPONSOR"
    PREMIUM = "PREMIUM"
    PROMOTIONAL = "PROMOTIONAL"
    INTERNAL_TEST = "INTERNAL_TEST"
    ADMIN_EXEMPT = "ADMIN_EXEMPT"


class MediaType(StrEnum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"


class LedgerDirection(StrEnum):
    GRANT = "GRANT"
    RESERVE = "RESERVE"
    CONSUME = "CONSUME"
    RELEASE = "RELEASE"
    ADJUST = "ADJUST"


class FundingDecision(StrEnum):
    FUNDED = "FUNDED"
    REWARDED_AD_REQUIRED = "REWARDED_AD_REQUIRED"
    PREMIUM_OPTION = "PREMIUM_OPTION"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class CloudCreditAccount:
    account_id: str
    balance: int = 0


@dataclass(frozen=True)
class CloudCreditLedgerEntry:
    entry_id: str
    account_id: str
    direction: LedgerDirection
    amount: int
    funding_source: FundingSource | None = None


@dataclass(frozen=True)
class CostProfile:
    operation_type: str
    cost_class: str
    estimated_cost: int


@dataclass(frozen=True)
class SpeciesCapabilityPack:
    species: str
    version: str
    supported_analysis_types: tuple[str, ...] = ()
    enabled_analysis_types: tuple[str, ...] = ()
    safety_policy_version: str = "0"
    public_enabled: bool = False
