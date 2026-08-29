"""Local billing abuse-contract checks; no Google Play credentials required."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.billing.premium import PremiumError, PremiumService


def main() -> int:
    service = PremiumService(verifier=lambda body: body.get("verification_source") == "LOCAL_TEST", expected_package_name="com.peti.app", local_test_mode=True)
    base = {"product_id": "peti_premium_monthly", "purchase_token": "token-a", "play_state": "PURCHASED", "package_name": "com.peti.app", "verification_source": "LOCAL_TEST"}
    service.reconcile("owner-a", base)
    try:
        service.reconcile("owner-b", base)
        return 1
    except PremiumError as exc:
        assert str(exc) == "PREMIUM_PURCHASE_TOKEN_CONFLICT"
    try:
        service.reconcile("owner-c", {**base, "purchase_token": "token-c", "product_id": "forged"})
        return 1
    except PremiumError as exc:
        assert str(exc) == "PREMIUM_PRODUCT_NOT_ALLOWED"
    try:
        service.reconcile("owner-c", {**base, "purchase_token": "token-c", "package_name": "com.attacker.app"})
        return 1
    except PremiumError as exc:
        assert str(exc) == "PREMIUM_PACKAGE_NOT_ALLOWED"
    try:
        service.reconcile("owner-c", {**base, "purchase_token": "token-c", "verification_source": "FORGED"})
        return 1
    except PremiumError as exc:
        assert str(exc) == "PREMIUM_VERIFICATION_FAILED"
    duplicate = service.reconcile("owner-a", {**base, "event_id": "event-1"})
    replay = service.reconcile("owner-a", {**base, "event_id": "event-1", "play_state": "EXPIRED"})
    assert duplicate.id == replay.id and replay.entitlement_state == "ACTIVE"
    print("BILLING_SECURITY=PASS replay_cross_account_product_and_forgery")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
