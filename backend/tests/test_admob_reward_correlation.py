from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

from app.advertising.domain import RewardIntentStatus
from app.advertising.service import RewardService
from app.credits.service import CreditService


class SignedValues:
    def verify(self, query):
        return {
            "transaction_id": "tx-1",
            "custom_data": "intent-1",
            "user_id": "user-1",
            "reward_amount": "1",
        }


def test_admob_ssv_correlates_intent_user_and_amount_before_granting():
    credits = CreditService()
    rewards = RewardService(credits, SignedValues())
    intent = rewards.create_intent("user-1", "ADMOB")
    rewards.intents["intent-1"] = rewards.intents.pop(intent.id)
    assert rewards.verify_google_query("signed") == ("VERIFIED", 1)


def test_admob_ssv_rejects_wrong_user_without_granting():
    class WrongUser(SignedValues):
        def verify(self, query):
            values = super().verify(query)
            values["user_id"] = "other-user"
            return values

    credits = CreditService()
    rewards = RewardService(credits, WrongUser())
    intent = rewards.create_intent("user-1", "ADMOB")
    rewards.intents["intent-1"] = rewards.intents.pop(intent.id)
    assert rewards.verify_google_query("signed") == ("REWARD_VERIFICATION_FAILED", 0)
    assert not credits.grants


def test_reward_intent_expiry_uses_injected_clock_boundary():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    current = [now]
    credits = CreditService()
    rewards = RewardService(credits, SignedValues(), clock=lambda: current[0])
    intent = rewards.create_intent("user-1", "ADMOB")
    rewards.intents["intent-1"] = rewards.intents.pop(intent.id)
    current[0] = now + timedelta(minutes=10)
    assert rewards.verify_google_query("signed") == ("REWARD_INTENT_EXPIRED", 0)
    assert not credits.grants


def test_reward_google_callback_is_atomic_for_duplicate_delivery():
    credits = CreditService()
    rewards = RewardService(credits, SignedValues())
    intent = rewards.create_intent("user-1", "ADMOB")
    rewards.intents["intent-1"] = rewards.intents.pop(intent.id)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(rewards.verify_google_query, ["signed", "signed"]))
    assert sorted(results) == [("REWARD_ALREADY_GRANTED", 0), ("VERIFIED", 1)]
    assert len(credits.grants) == 1


def test_malformed_reward_amount_persists_invalid_intent():
    class MalformedAmount(SignedValues):
        def verify(self, query):
            values = super().verify(query)
            values["reward_amount"] = "not-an-integer"
            return values

    rewards = RewardService(CreditService(), MalformedAmount())
    intent = rewards.create_intent("user-1", "ADMOB")
    values = rewards.intents.pop(intent.id)
    values.id = "intent-1"
    rewards.intents[values.id] = values
    assert rewards.verify_google_query("signed") == ("REWARD_VERIFICATION_FAILED", 0)
    assert values.status == RewardIntentStatus.INVALID


def test_reward_intent_and_transaction_hydrate_after_restart():
    class Store:
        def __init__(self):
            self.rows = {}

        def append(self, collection, key, data):
            self.rows[(collection, key)] = dict(data)

        def list_all(self, collection):
            return [data for (name, _), data in self.rows.items() if name == collection]

    store = Store()
    credits = CreditService()
    first = RewardService(credits, SignedValues(), store=store)
    intent = first.create_intent("user-1", "ADMOB")
    first.intents.pop(intent.id)
    intent.id = "intent-1"
    first.intents[intent.id] = intent
    first._save_intent(intent)
    assert first.verify_google_query("signed") == ("VERIFIED", 1)
    restarted = RewardService(credits, SignedValues(), store=store)
    assert intent.id in restarted.intents
    assert "tx-1" in restarted.provider_transactions
    assert restarted.verify_google_query("signed") == ("REWARD_ALREADY_GRANTED", 0)
