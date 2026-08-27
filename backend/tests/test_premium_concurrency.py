from concurrent.futures import ThreadPoolExecutor

import pytest
from app.billing.google_play import PremiumEntitlementState
from app.billing.premium import PremiumError, PremiumService


def test_concurrent_purchase_reconciliation_creates_one_entitlement():
    service = PremiumService(local_test_mode=True, allowed_product_ids={"peti_premium_monthly"})

    def reconcile(index):
        return service.reconcile("u", {
            "product_id": "peti_premium_monthly",
            "purchase_token": "same-token",
            "play_state": "PURCHASED",
            "event_id": f"event-{index}",
            "_trusted_verification": True,
        })

    with ThreadPoolExecutor(max_workers=8) as pool:
        values = list(pool.map(reconcile, range(8)))
    assert len(service.entitlements) == 1
    assert all(value.id == values[0].id for value in values)
    assert service.current("u").commercial_tier == "PREMIUM"
    assert len(service.allowance_grants) == 1
    assert next(iter(service.allowance_grants.values())).units == 20


def test_reconciliation_requires_exact_configured_package_name():
    service = PremiumService(
        local_test_mode=True,
        allowed_product_ids={"peti_premium_monthly"},
        expected_package_name="com.peti.app",
    )
    body = {
        "product_id": "peti_premium_monthly",
        "purchase_token": "token-package-check",
        "play_state": "PURCHASED",
        "_trusted_verification": True,
    }
    with pytest.raises(PremiumError, match="PREMIUM_PACKAGE_NOT_ALLOWED"):
        service.reconcile("u", body)
    body["package_name"] = "com.other.app"
    with pytest.raises(PremiumError, match="PREMIUM_PACKAGE_NOT_ALLOWED"):
        service.reconcile("u", body)
    body["package_name"] = "com.peti.app"
    assert service.reconcile("u", body).commercial_tier == "PREMIUM"


@pytest.mark.parametrize(
    ("play_state", "expected_state", "expected_tier"),
    [
        ("PURCHASED", PremiumEntitlementState.ACTIVE, "PREMIUM"),
        ("GRACE", PremiumEntitlementState.IN_GRACE_PERIOD, "PREMIUM"),
        ("ON_HOLD", PremiumEntitlementState.ON_HOLD, "FREE"),
        ("CANCELED", PremiumEntitlementState.CANCELED_ENTITLED, "PREMIUM"),
        ("EXPIRED", PremiumEntitlementState.EXPIRED, "FREE"),
        ("REVOKED", PremiumEntitlementState.REVOKED, "FREE"),
    ],
)
def test_subscription_state_matrix_is_fail_closed_and_preserves_paid_canceled_access(
    play_state, expected_state, expected_tier
):
    service = PremiumService(local_test_mode=True, allowed_product_ids={"peti_premium_monthly"})
    item = service.reconcile(
        "u",
        {
            "product_id": "peti_premium_monthly",
            "purchase_token": f"token-{play_state}",
            "play_state": play_state,
            "_trusted_verification": True,
        },
    )
    assert item.entitlement_state == expected_state.value
    assert item.commercial_tier == expected_tier


def test_purchase_token_replay_cannot_cross_accounts():
    service = PremiumService(local_test_mode=True, allowed_product_ids={"peti_premium_monthly"})
    body = {
        "product_id": "peti_premium_monthly",
        "purchase_token": "token-owner-a",
        "play_state": "PURCHASED",
        "_trusted_verification": True,
    }
    service.reconcile("owner-a", body)
    with pytest.raises(PremiumError, match="PREMIUM_PURCHASE_TOKEN_CONFLICT"):
        service.reconcile("owner-b", body)


def test_non_local_mode_rejects_forged_trusted_verification_marker():
    service = PremiumService(local_test_mode=False, allowed_product_ids={"peti_premium_monthly"})
    with pytest.raises(PremiumError, match="PREMIUM_VERIFICATION_FAILED"):
        service.reconcile("owner", {
            "product_id": "peti_premium_monthly",
            "purchase_token": "forged-token",
            "_trusted_verification": True,
        })


def test_verified_entitlement_rejects_coercive_acknowledgement_fields():
    service = PremiumService(local_test_mode=True, allowed_product_ids={"peti_premium_monthly"})

    with pytest.raises(PremiumError, match="PREMIUM_VERIFICATION_FAILED"):
        service.reconcile("owner", {
            "product_id": "peti_premium_monthly",
            "purchase_token": "token-ack-invalid",
            "_trusted_verification": True,
            "acknowledged": "false",
        })


def test_reconcile_rejects_non_string_purchase_identifiers():
    service = PremiumService(local_test_mode=True, allowed_product_ids={"peti_premium_monthly"})

    with pytest.raises(PremiumError, match="PREMIUM_PURCHASE_INVALID"):
        service.reconcile("owner", {
            "product_id": "peti_premium_monthly",
            "purchase_token": None,
            "_trusted_verification": True,
        })


def test_reconcile_rejects_malformed_event_identifier():
    service = PremiumService(local_test_mode=True, allowed_product_ids={"peti_premium_monthly"})

    with pytest.raises(PremiumError, match="PREMIUM_EVENT_INVALID"):
        service.reconcile("owner", {
            "product_id": "peti_premium_monthly",
            "purchase_token": "token-event-invalid",
            "event_id": [],
            "_trusted_verification": True,
        })
