from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock


@dataclass(frozen=True)
class PremiumAllowancePolicy:
    id: str = "premium-allowance-v1"
    version: str = "1.0.0"
    monthly_units: int = 20
    max_single_operation_units: int = 3
    ads_required: bool = False


@dataclass(frozen=True)
class AllowanceGrant:
    owner_user_id: str
    period_key: str
    units: int
    policy_id: str
    created_at: datetime


class PremiumAllowanceService:
    """Idempotent premium-period allowance materialization."""
    def __init__(self, policy: PremiumAllowancePolicy | None = None):
        self.policy = policy or PremiumAllowancePolicy()
        self.grants: dict[tuple[str, str], AllowanceGrant] = {}
        self.lock = RLock()

    def grant_for_period(self, owner: str, period_key: str) -> AllowanceGrant:
        key = (owner, period_key)
        with self.lock:
            if key not in self.grants:
                self.grants[key] = AllowanceGrant(owner, period_key, self.policy.monthly_units, self.policy.id, datetime.now(UTC))
            return self.grants[key]


class PremiumReconciliationService:
    def __init__(self, premium_service, publisher): self.premium_service, self.publisher = premium_service, publisher
    def reconcile_verified(self, owner, package_name, body):
        verified = self.publisher.verify(package_name, body["product_id"], body["purchase_token"])
        return self.premium_service.reconcile(owner, {**body, **verified, "_trusted_verification": True})
