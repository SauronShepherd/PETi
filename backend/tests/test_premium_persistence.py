from datetime import UTC, datetime

from app.billing.premium import PremiumEntitlement, PremiumService


def test_premium_entitlement_hydrates_serialized_timestamps():
    instant = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)

    class Store:
        def all(self, collection):
            return [{
                "id": "entitlement-1", "owner_user_id": "owner-1", "product_id": "peti_premium_monthly",
                "purchase_token": "purchase-token", "play_state": "PURCHASED", "commercial_tier": "PREMIUM",
                "entitlement_until": instant.isoformat(), "created_at": instant.isoformat(), "updated_at": instant.isoformat(),
            }] if collection == "premium_entitlements" else []

    service = PremiumService(store=Store(), local_test_mode=True, allowed_product_ids={"peti_premium_monthly"})
    entitlement = service.entitlements["entitlement-1"]
    assert entitlement.entitlement_until == instant
    assert entitlement.updated_at == instant


def test_premium_public_response_redacts_purchase_token():
    entitlement = PremiumEntitlement(
        "entitlement-1", "owner-1", "peti_premium_monthly", "secret-purchase-token",
        "PURCHASED", "PREMIUM",
    )
    payload = PremiumService.public(entitlement)
    assert "purchase_token" not in payload
    assert payload["product_id"] == "peti_premium_monthly"


def test_current_entitlement_fails_closed_after_entitlement_deadline():
    instant = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
    service = PremiumService(clock=lambda: instant, local_test_mode=True, allowed_product_ids={"peti_premium_monthly"})
    item = service.reconcile(
        "owner-1",
        {
            "product_id": "peti_premium_monthly", "purchase_token": "expired-token",
            "play_state": "PURCHASED", "entitlement_until": instant,
            "_trusted_verification": True,
        },
    )
    assert item.commercial_tier == "PREMIUM"
    assert service.current("owner-1").commercial_tier == "FREE"
