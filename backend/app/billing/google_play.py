import hashlib
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar
from urllib.parse import quote


class PremiumEntitlementState(StrEnum):
    NONE = "NONE"
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    IN_GRACE_PERIOD = "IN_GRACE_PERIOD"
    ON_HOLD = "ON_HOLD"
    CANCELED_ENTITLED = "CANCELED_ENTITLED"
    PAUSED = "PAUSED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    UNKNOWN_REQUIRES_RECONCILIATION = "UNKNOWN_REQUIRES_RECONCILIATION"


@dataclass(frozen=True)
class GooglePlaySubscriptionPurchase:
    purchase_token_hash: str
    user_id: str
    product_id: str
    state: str
    acknowledged: bool


class GooglePlaySubscriptionStateMapper:
    STATES: ClassVar[dict[str, PremiumEntitlementState]] = {
        "PURCHASED": PremiumEntitlementState.ACTIVE,
        "ACTIVE": PremiumEntitlementState.ACTIVE,
        "GRACE": PremiumEntitlementState.IN_GRACE_PERIOD,
        "IN_GRACE_PERIOD": PremiumEntitlementState.IN_GRACE_PERIOD,
        "PENDING": PremiumEntitlementState.PENDING,
        "ON_HOLD": PremiumEntitlementState.ON_HOLD,
        "PAUSED": PremiumEntitlementState.PAUSED,
        "CANCELED": PremiumEntitlementState.CANCELED_ENTITLED,
        "CANCELED_ENTITLED": PremiumEntitlementState.CANCELED_ENTITLED,
        "EXPIRED": PremiumEntitlementState.EXPIRED,
        "REVOKED": PremiumEntitlementState.REVOKED,
    }
    def map_state(self, state: str | None) -> PremiumEntitlementState:
        normalized = str(state or "").upper()
        normalized = normalized.removeprefix("SUBSCRIPTION_STATE_")
        return self.STATES.get(normalized, PremiumEntitlementState.UNKNOWN_REQUIRES_RECONCILIATION)
    def map(self, state: str) -> str:
        return "PREMIUM" if self.map_state(state) in {PremiumEntitlementState.ACTIVE, PremiumEntitlementState.IN_GRACE_PERIOD} else "FREE"


@dataclass(frozen=True)
class SubscriptionPurchaseV2:
    package_name: str
    product_id: str
    purchase_token: str
    state: PremiumEntitlementState
    entitlement_until: object | None = None
    acknowledgement_state: str = "ACKNOWLEDGEMENT_STATE_UNSPECIFIED"
    linked_purchase_token: str | None = None

    @classmethod
    def from_verified(cls, body: dict) -> "SubscriptionPurchaseV2":
        package_name = body.get("package_name", "")
        product_id = body.get("product_id", "")
        purchase_token = body.get("purchase_token", "")
        if not all(
            isinstance(value, str) and value.strip()
            for value in (package_name, product_id, purchase_token)
        ):
            raise ValueError("PREMIUM_VERIFICATION_INVALID")
        state = GooglePlaySubscriptionStateMapper().map_state(body.get("subscription_state", body.get("play_state")))
        return cls(package_name, product_id, purchase_token, state, body.get("entitlement_until"), str(body.get("acknowledgement_state", "ACKNOWLEDGEMENT_STATE_UNSPECIFIED")), body.get("linked_purchase_token"))


@dataclass(frozen=True)
class GooglePlayRtdnEvent:
    event_id: str
    purchase_token: str
    product_id: str
    subscription_state: str

    @classmethod
    def from_payload(cls, payload: dict) -> "GooglePlayRtdnEvent":
        if not isinstance(payload, dict):
            raise ValueError("RTDN_PAYLOAD_INVALID")  # noqa: TRY004
        event_id = payload.get("event_id", "")
        token = payload.get("purchase_token", "")
        product = payload.get("product_id", "")
        state = payload.get("subscription_state", "")
        if not all(isinstance(value, str) for value in (event_id, token, product, state)):
            raise ValueError("RTDN_PAYLOAD_INVALID")
        if not all((event_id, token, product, state)):
            raise ValueError("RTDN_PAYLOAD_INVALID")
        return cls(event_id, token, product, state)


class GooglePlayPublisherGateway:
    """Authenticated Google Play subscriptionsv2 lookup boundary.

    The HTTP session is injectable so contract tests never contact Google.
    Credentials are resolved lazily at construction when no session is given.
    """
    BASE_URL = "https://androidpublisher.googleapis.com/androidpublisher/v3"

    def __init__(self, package_name: str | None = None, http_session=None, credentials=None):
        self.package_name = package_name
        if http_session is not None:
            self.http_session = http_session
        else:
            import google.auth
            from google.auth.transport.requests import AuthorizedSession

            resolved, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/androidpublisher"]
            )
            self.http_session = AuthorizedSession(credentials or resolved)

    def verify(self, package_name, product_id, purchase_token):
        if not all(
            isinstance(value, str) and value.strip()
            for value in (package_name, product_id, purchase_token)
        ):
            raise ValueError("PREMIUM_PURCHASE_INVALID")
        if self.package_name and package_name != self.package_name:
            raise ValueError("PREMIUM_PACKAGE_NOT_ALLOWED")
        url = (
            f"{self.BASE_URL}/applications/{quote(package_name, safe='')}/"
            f"purchases/subscriptionsv2/tokens/{quote(purchase_token, safe='')}"
        )
        response = self.http_session.get(url, timeout=15)
        if getattr(response, "status_code", None) != 200:
            raise ValueError("GOOGLE_PLAY_VERIFICATION_FAILED")
        body = response.json()
        line_items = body.get("lineItems") or []
        products = {str(item.get("productId", "")) for item in line_items}
        if product_id not in products:
            raise ValueError("PREMIUM_PRODUCT_NOT_ALLOWED")
        return {
            "package_name": package_name,
            "product_id": product_id,
            "purchase_token": purchase_token,
            "subscription_state": body.get("subscriptionState"),
            "acknowledgement_state": body.get("acknowledgementState"),
            "line_items": line_items,
            "raw": body,
        }


class GooglePlayPublisherVerifier:
    """Callable PremiumService verifier backed by the canonical Play lookup."""

    def __init__(self, gateway: GooglePlayPublisherGateway):
        self.gateway = gateway

    def __call__(self, body: dict) -> bool:
        package_name = body.get("package_name", "")
        product_id = body.get("product_id", "")
        token = body.get("purchase_token", "")
        canonical = self.gateway.verify(package_name, product_id, token)
        body["play_state"] = canonical["subscription_state"]
        body["acknowledgement_state"] = canonical["acknowledgement_state"]
        return True


class PlayBillingGateway:
    """Backend-neutral Android billing seam; raw BillingClient types stay on Android."""
    def product_ids(self): return ["peti_premium_monthly", "peti_premium_yearly"]


def token_hash(token: str) -> str: return hashlib.sha256(token.encode()).hexdigest()
