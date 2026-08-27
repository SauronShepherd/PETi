from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class AbuseDecision:
    allowed: bool
    code: str
    retry_after_seconds: int = 0


class AbuseGuard:
    def __init__(self, max_requests: int = 20, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.events: dict[str, list[datetime]] = {}

    def check_and_record(self, user_id: str) -> AbuseDecision:
        now = datetime.now(UTC)
        recent = [x for x in self.events.get(user_id, []) if now - x < self.window]
        if len(recent) >= self.max_requests:
            retry = int((self.window - (now - recent[0])).total_seconds())
            return AbuseDecision(False, "FUNDING_RATE_LIMITED", max(1, retry))
        recent.append(now)
        self.events[user_id] = recent
        return AbuseDecision(True, "OK")


@dataclass(frozen=True)
class RetentionCategory:
    name: str
    description: str
    customer_visible: bool


RETENTION_CATEGORIES = (
    RetentionCategory("CUSTOMER_CREDIT_HISTORY", "Visible balance and credit events", True),
    RetentionCategory("OPERATIONAL_LEDGER", "Immutable accounting evidence", False),
    RetentionCategory("PROVIDER_VERIFICATION", "Replay and verification evidence", False),
    RetentionCategory("SECURITY_FRAUD", "Abuse and security evidence", False),
)
