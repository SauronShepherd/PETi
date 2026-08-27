"""Shared bounded, idempotent reconciliation primitives for platform domains."""
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock

DOMAINS = ("analysis", "funding", "reward", "billing", "report", "deletion", "notification")


@dataclass
class ReconciliationResult:
    domain: str
    operation_key: str
    status: str
    pending: list[str] = field(default_factory=list)
    completed_at: str | None = None


class ReconciliationService:
    """Run one bounded action per idempotency key and retain its outcome.

    The service deliberately stores only identifiers and statuses. Domain adapters
    own payloads and persistence; replaying a completed key never invokes the
    adapter again.
    """
    def __init__(self):
        self._results: dict[tuple[str, str], ReconciliationResult] = {}
        self._lock = RLock()

    def reconcile(self, domain: str, operation_key: str, action: Callable[[], list[str] | None]) -> ReconciliationResult:
        if domain not in DOMAINS:
            raise ValueError("RECONCILIATION_DOMAIN_INVALID")
        if not operation_key or len(operation_key) > 200:
            raise ValueError("RECONCILIATION_KEY_INVALID")
        identity = (domain, operation_key)
        with self._lock:
            previous = self._results.get(identity)
            if previous and previous.status == "COMPLETE":
                return previous
            pending = [str(item) for item in (action() or [])]
            result = ReconciliationResult(
                domain=domain,
                operation_key=operation_key,
                status="PENDING" if pending else "COMPLETE",
                pending=pending,
                completed_at=None if pending else datetime.now(UTC).isoformat(),
            )
            self._results[identity] = result
            return result

    def snapshot(self) -> list[ReconciliationResult]:
        with self._lock:
            return list(self._results.values())
