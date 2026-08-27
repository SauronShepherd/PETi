from dataclasses import asdict
from datetime import UTC, datetime
from threading import RLock
from typing import ClassVar

from app.credits.domain import FundingSource

from .domain import RewardIntent, RewardIntentStatus, new_intent


class RewardService:
    ALLOWED_PROVIDERS: ClassVar[set[str]] = {"FAKE", "ADMOB"}

    def __init__(self, credits, verifier=None, clock=None, store=None):
        self.credits = credits
        self.verifier = verifier
        self.store = store
        self.clock = clock or (lambda: datetime.now(UTC))
        self.intents: dict[str, RewardIntent] = {}
        self.provider_transactions: set[str] = set()
        self.lock = RLock()
        self._hydrate()

    def _hydrate(self):
        if not self.store or not hasattr(self.store, "list_all"):
            return
        try:
            intent_rows = self.store.list_all("reward_intents")
        except Exception:  # noqa: BLE001 - unavailable reward journal must not crash startup
            intent_rows = []
        for raw in intent_rows:
            try:
                data = dict(raw)
                for key in ("created_at", "expires_at", "verified_at"):
                    value = data.get(key)
                    if value is not None and not isinstance(value, datetime):
                        data[key] = datetime.fromisoformat(str(value))
                data["status"] = RewardIntentStatus(data["status"])
                intent = RewardIntent(**data)
                self.intents[intent.id] = intent
            except (KeyError, TypeError, ValueError):
                continue
        try:
            transaction_rows = self.store.list_all("reward_provider_transactions")
        except Exception:  # noqa: BLE001 - unavailable dedupe journal must not crash startup
            transaction_rows = []
        for raw in transaction_rows:
            transaction_id = raw.get("id") if isinstance(raw, dict) else None
            if transaction_id:
                self.provider_transactions.add(transaction_id)

    def _save_intent(self, intent):
        if self.store and hasattr(self.store, "append"):
            self.store.append("reward_intents", intent.id, asdict(intent))

    def _save_transaction(self, transaction_id):
        if self.store and hasattr(self.store, "append"):
            self.store.append("reward_provider_transactions", transaction_id, {"id": transaction_id})

    def create_intent(self, user_id: str, provider: str = "FAKE") -> RewardIntent:
        with self.lock:
            provider = str(provider).upper()
            if provider not in self.ALLOWED_PROVIDERS:
                raise ValueError("REWARD_PROVIDER_NOT_SUPPORTED")
            intent = new_intent(user_id, 1, provider, now=self.clock())
            self.intents[intent.id] = intent
            self._save_intent(intent)
            return intent

    def get_intent(self, user_id: str, intent_id: str) -> RewardIntent | None:
        with self.lock:
            intent = self.intents.get(intent_id)
            return intent if intent and intent.user_id == user_id else None

    def verify_callback(self, provider: str, transaction_id: str, intent_id: str, signature: str):
        with self.lock:
            intent = self.intents.get(intent_id)
            if not intent or intent.provider != str(provider).upper():
                return "REWARD_VERIFICATION_FAILED", 0
            if intent.expires_at <= self.clock():
                if intent:
                    intent.status = RewardIntentStatus.EXPIRED
                    self._save_intent(intent)
                return "REWARD_INTENT_EXPIRED", 0
            if transaction_id in self.provider_transactions:
                return "REWARD_ALREADY_GRANTED", 0
            if signature != intent.nonce:
                intent.status = RewardIntentStatus.INVALID
                self._save_intent(intent)
                return "REWARD_VERIFICATION_FAILED", 0
            grant = self.credits.grant(
                intent.user_id,
                FundingSource.REWARDED_AD,
                intent.expected_credit_amount,
                source_reference=intent.id,
                idempotency_key=f"reward:{transaction_id}",
            )
            self.provider_transactions.add(transaction_id)
            self._save_transaction(transaction_id)
            intent.status = RewardIntentStatus.GRANTED
            intent.grant_id = grant.id
            intent.verified_at = self.clock()
            self._save_intent(intent)
            return "VERIFIED", intent.expected_credit_amount

    def verify_google_query(self, query: str):
        with self.lock:
            return self._verify_google_query(query)

    def _verify_google_query(self, query: str):
        if not self.verifier:
            return "FUNDING_TEMPORARILY_UNAVAILABLE", 0
        values = self.verifier.verify(query)
        transaction_id = values.get("transaction_id", "")
        intent_id = values.get("custom_data", "")
        user_id = values.get("user_id", "")
        intent = self.intents.get(intent_id)
        if not transaction_id or not intent or intent.provider != "ADMOB":
            return "REWARD_VERIFICATION_FAILED", 0
        if intent.user_id != user_id:
            intent.status = RewardIntentStatus.INVALID
            self._save_intent(intent)
            return "REWARD_VERIFICATION_FAILED", 0
        if "reward_amount" in values:
            try:
                if int(values["reward_amount"]) != intent.expected_credit_amount:
                    intent.status = RewardIntentStatus.INVALID
                    self._save_intent(intent)
                    return "REWARD_VERIFICATION_FAILED", 0
            except ValueError:
                intent.status = RewardIntentStatus.INVALID
                self._save_intent(intent)
                return "REWARD_VERIFICATION_FAILED", 0
        if transaction_id in self.provider_transactions:
            return "REWARD_ALREADY_GRANTED", 0
        if intent.expires_at <= self.clock():
            intent.status = RewardIntentStatus.EXPIRED
            self._save_intent(intent)
            return "REWARD_INTENT_EXPIRED", 0
        grant = self.credits.grant(
            intent.user_id,
            FundingSource.REWARDED_AD,
            intent.expected_credit_amount,
            source_reference=intent.id,
            idempotency_key=f"reward:{transaction_id}",
        )
        self.provider_transactions.add(transaction_id)
        self._save_transaction(transaction_id)
        intent.status = RewardIntentStatus.GRANTED
        intent.grant_id = grant.id
        intent.verified_at = self.clock()
        self._save_intent(intent)
        return "VERIFIED", intent.expected_credit_amount
