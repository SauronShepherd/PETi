"""Trusted Google Play RTDN boundary with replay-safe event handling."""
from dataclasses import dataclass
from threading import RLock

from .google_play import GooglePlayRtdnEvent


@dataclass(frozen=True)
class RtdnResult:
    event_id: str
    status: str
    owner_user_id: str | None = None


class GooglePlayRtdnReceiver:
    """Accept normalized, already-authenticated RTDN events.

    Authentication of the Pub/Sub push envelope belongs to the HTTP adapter;
    this boundary only accepts a trusted event and resolves its token to the
    owning account before invoking the single premium reconciliation path.
    """
    def __init__(self, premium_service, owner_for_token):
        self.premium_service = premium_service
        self.owner_for_token = owner_for_token
        self._seen: set[str] = set()
        self._lock = RLock()

    def receive(self, payload: dict) -> RtdnResult:
        event = GooglePlayRtdnEvent.from_payload(payload)
        with self._lock:
            if event.event_id in self._seen:
                return RtdnResult(event.event_id, "DUPLICATE")
            owner = self.owner_for_token(event.purchase_token)
            if not owner:
                raise ValueError("RTDN_OWNER_NOT_FOUND")
            self.premium_service.reconcile_rtdn(owner, {
                "event_id": event.event_id,
                "purchase_token": event.purchase_token,
                "product_id": event.product_id,
                "subscription_state": event.subscription_state,
            })
            self._seen.add(event.event_id)
            return RtdnResult(event.event_id, "RECONCILED", owner)
