"""Backend-authoritative Google Play Premium entitlement boundary."""
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from threading import RLock
from uuid import uuid4

from .google_play import (
    GooglePlayRtdnEvent,
    GooglePlaySubscriptionStateMapper,
    PlayBillingGateway,
    PremiumEntitlementState,
)
from .policy import PremiumAllowanceService


class PremiumError(ValueError):
    pass


@dataclass
class PremiumEntitlement:
    id: str
    owner_user_id: str
    product_id: str
    purchase_token: str
    play_state: str
    commercial_tier: str
    entitlement_until: datetime | None = None
    acknowledged: bool = False
    allowance_policy_id: str = "premium-v1"
    entitlement_state: str = PremiumEntitlementState.UNKNOWN_REQUIRES_RECONCILIATION.value
    acknowledgement_attempted: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class PremiumService:
    def __init__(self, store=None, verifier=None, clock=None, allowed_product_ids=None, expected_package_name=None, local_test_mode=False, rtdn_verifier=None, allowance_service=None):
        self.store, self.verifier = store, verifier
        self.allowed_product_ids = set(allowed_product_ids or PlayBillingGateway().product_ids())
        self.expected_package_name = expected_package_name
        self.local_test_mode = local_test_mode
        self.rtdn_verifier = rtdn_verifier
        self.clock = clock or (lambda: datetime.now(UTC))
        self.entitlements: dict[str, PremiumEntitlement] = {}
        self.tokens: dict[str, str] = {}
        self.events: set[str] = set()
        self.lock = RLock()
        self.allowance_service = allowance_service or PremiumAllowanceService()
        self.allowance_grants = {}
        self._hydrate()

    def _grant_allowance_if_entitled(self, owner: str, state: PremiumEntitlementState):
        if state not in {PremiumEntitlementState.ACTIVE, PremiumEntitlementState.IN_GRACE_PERIOD}:
            return None
        period = self.clock().astimezone(UTC).strftime("%Y-%m")
        grant = self.allowance_service.grant_for_period(owner, period)
        self.allowance_grants[(owner, period)] = grant
        return grant

    def _hydrate(self):
        if not self.store or not hasattr(self.store, "all"):
            return
        try:
            rows = self.store.all("premium_entitlements")
        except Exception:  # noqa: BLE001 - unavailable entitlement state must fail closed
            rows = []
        for data in rows:
            try:
                data = dict(data)
                for key in ("entitlement_until", "created_at", "updated_at"):
                    value = data.get(key)
                    if value is not None and not isinstance(value, datetime):
                        data[key] = datetime.fromisoformat(str(value))
                item = PremiumEntitlement(**{
                    key: data[key] for key in PremiumEntitlement.__dataclass_fields__ if key in data
                })
                self.entitlements[item.id] = item
                self.tokens[item.purchase_token] = item.id
            except (KeyError, TypeError, ValueError):
                continue

    def _save(self, value):
        if self.store and hasattr(self.store, "put_raw"):
            self.store.put_raw("premium_entitlements", value.id, asdict(value))

    def reconcile(self, owner, body):
        """Reconcile one purchase atomically under the service lock."""
        with self.lock:
            return self._reconcile_locked(owner, body)

    def _reconcile_locked(self, owner, body):
        product_id = body.get("product_id", ""); token = body.get("purchase_token", ""); event_id = body.get("event_id")
        if not all(isinstance(value, str) and value.strip() for value in (product_id, token)):
            raise PremiumError("PREMIUM_PURCHASE_INVALID")
        if event_id is not None and (not isinstance(event_id, str) or not event_id.strip()):
            raise PremiumError("PREMIUM_EVENT_INVALID")
        if product_id not in self.allowed_product_ids:
            raise PremiumError("PREMIUM_PRODUCT_NOT_ALLOWED")
        if self.expected_package_name and body.get("package_name") != self.expected_package_name:
            raise PremiumError("PREMIUM_PACKAGE_NOT_ALLOWED")
        if event_id and event_id in self.events and token in self.tokens:
            return self.entitlements[self.tokens[token]]
        if token in self.tokens:
            current = self.entitlements[self.tokens[token]]
            if current.owner_user_id != owner: raise PremiumError("PREMIUM_PURCHASE_TOKEN_CONFLICT")
            verified = self.verifier(body) if self.verifier else (self.local_test_mode and body.get("_trusted_verification") is True)
            if not verified:
                raise PremiumError("PREMIUM_VERIFICATION_FAILED")
            state = GooglePlaySubscriptionStateMapper().map_state(body.get("play_state", body.get("subscription_state")))
            current.play_state = str(body.get("play_state", body.get("subscription_state", current.play_state)))
            current.entitlement_state = state.value
            current.commercial_tier = "PREMIUM" if state in {PremiumEntitlementState.ACTIVE, PremiumEntitlementState.IN_GRACE_PERIOD, PremiumEntitlementState.CANCELED_ENTITLED} else "FREE"
            if body.get("entitlement_until") is not None:
                current.entitlement_until = body["entitlement_until"]
            current.updated_at = self.clock()
            if event_id:
                self.events.add(event_id)
            self._save(current)
            self._grant_allowance_if_entitled(owner, state)
            return current
        # Never trust a client-supplied verified flag. Local emulator tests
        # must use an explicit test-only verifier; production fails closed.
        verified = self.verifier(body) if self.verifier else (self.local_test_mode and body.get("_trusted_verification") is True)
        if not verified:
            raise PremiumError("PREMIUM_VERIFICATION_FAILED")
        acknowledged = body.get("acknowledged", True)
        acknowledgement_attempted = body.get("acknowledgement_attempted", False)
        if not isinstance(acknowledged, bool) or not isinstance(acknowledgement_attempted, bool):
            raise PremiumError("PREMIUM_VERIFICATION_FAILED")
        play_state = str(body.get("play_state", body.get("subscription_state", "PURCHASED")))
        entitlement_state = GooglePlaySubscriptionStateMapper().map_state(play_state)
        # A canceled subscription remains entitled through its paid period;
        # it must not be downgraded merely because Play reports CANCELED.
        entitled = entitlement_state in {
            PremiumEntitlementState.ACTIVE,
            PremiumEntitlementState.IN_GRACE_PERIOD,
            PremiumEntitlementState.CANCELED_ENTITLED,
        }
        now = self.clock()
        item = PremiumEntitlement(str(uuid4()), owner, product_id, token, play_state, "PREMIUM" if entitled else "FREE", body.get("entitlement_until"), acknowledged=acknowledged, entitlement_state=entitlement_state.value, acknowledgement_attempted=acknowledgement_attempted, created_at=now, updated_at=now)
        self.entitlements[item.id] = item; self.tokens[token] = item.id
        if event_id: self.events.add(event_id)
        self._save(item)
        self._grant_allowance_if_entitled(owner, entitlement_state)
        return item

    def acknowledge_once(self, owner, purchase_token, acknowledge):
        with self.lock:
            item_id = self.tokens.get(purchase_token)
            item = self.entitlements.get(item_id) if item_id else None
            if not item or item.owner_user_id != owner:
                raise PremiumError("PREMIUM_PURCHASE_NOT_FOUND")
            if item.acknowledged:
                return item
            acknowledge(purchase_token)
            item.acknowledged = True
            item.acknowledgement_attempted = True
            item.updated_at = self.clock()
            self._save(item)
            return item

    def reconcile_rtdn(self, owner, payload):
        event = GooglePlayRtdnEvent.from_payload(payload)
        if not self.rtdn_verifier:
            raise PremiumError("GOOGLE_PLAY_RTDN_VERIFIER_NOT_CONFIGURED")
        canonical = self.rtdn_verifier(event.purchase_token, event.product_id)
        if not canonical or canonical.get("owner_user_id") != owner:
            raise PremiumError("PREMIUM_RTDN_CANONICAL_STATE_INVALID")
        return self.reconcile(owner, {
            "event_id": event.event_id,
            **canonical,
            "purchase_token": event.purchase_token,
            "product_id": event.product_id,
        })

    def current(self, owner):
        with self.lock:
            values = [x for x in self.entitlements.values() if x.owner_user_id == owner]
            if not values:
                return None
            item = max(values, key=lambda x: x.updated_at)
            if item.entitlement_until and item.entitlement_until <= self.clock():
                return replace(item, commercial_tier="FREE")
            return item

    @staticmethod
    def public(value):
        if not value:
            return {"commercial_tier": "FREE"}
        payload = asdict(value)
        payload.pop("purchase_token", None)
        return payload
