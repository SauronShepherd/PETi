from datetime import UTC, datetime

import pytest
from app.advertising.domain import RewardIntentStatus
from app.advertising.service import RewardService
from app.credits.service import CreditService


def test_reward_callback_is_idempotent_and_server_authoritative():
    credits = CreditService()
    rewards = RewardService(credits)
    intent = rewards.create_intent("u")
    first = rewards.verify_callback("FAKE", "tx-1", intent.id, intent.nonce)
    duplicate = rewards.verify_callback("FAKE", "tx-1", intent.id, intent.nonce)
    assert first == ("VERIFIED", 1) and duplicate == ("REWARD_ALREADY_GRANTED", 0)
    assert len([g for g in credits.grants.values() if g.user_id == "u"]) == 1


def test_invalid_reward_cannot_mint_credits():
    credits = CreditService()
    rewards = RewardService(credits)
    intent = rewards.create_intent("u")
    assert (
        rewards.verify_callback("FAKE", "tx-2", intent.id, "forged")[0]
        == "REWARD_VERIFICATION_FAILED"
    )
    assert not credits.grants


def test_credit_expiry_uses_injected_clock():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    credits = CreditService(clock=lambda: now)
    grant = credits.grant("u", "PROMOTIONAL", 2)
    from dataclasses import replace

    credits.grants[grant.id] = replace(grant, expires_at=now)
    assert credits.expire(now=now) == 1
    assert credits.grants[grant.id].remaining_amount == 0


def test_expired_reward_callback_persists_terminal_status():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    rewards = RewardService(CreditService(), clock=lambda: now)
    intent = rewards.create_intent("u")
    intent.expires_at = now
    assert rewards.verify_callback("FAKE", "tx-expired", intent.id, intent.nonce) == ("REWARD_INTENT_EXPIRED", 0)
    assert intent.status == RewardIntentStatus.EXPIRED


def test_reward_callback_requires_provider_binding_and_supported_provider():
    rewards = RewardService(CreditService())
    with pytest.raises(ValueError, match="REWARD_PROVIDER_NOT_SUPPORTED"):
        rewards.create_intent("u", "UNKNOWN")
    intent = rewards.create_intent("u", "FAKE")
    assert rewards.verify_callback("ADMOB", "tx-mismatch", intent.id, intent.nonce) == (
        "REWARD_VERIFICATION_FAILED", 0
    )
