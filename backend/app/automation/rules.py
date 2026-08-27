from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import uuid4


@dataclass
class AutomationRule:
    owner_user_id: str
    pet_id: str
    trigger: dict
    action: dict
    id: str = field(default_factory=lambda: str(uuid4()))
    enabled: bool = True
    version: int = 1
    last_fired_key: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class RuleEngine:
    def __init__(self, store: Any | None = None):
        self.store = store
        self.rules: dict[str, AutomationRule] = {}
        self.lock = RLock()
        self._hydrate()

    def _hydrate(self) -> None:
        if not self.store or not hasattr(self.store, "all"):
            return
        try:
            rows = self.store.all("automation_rules")
        except Exception:  # noqa: BLE001 - malformed/unavailable rules must not fire
            rows = []
        for row in rows:
            try:
                data = dict(row)
                if data.get("created_at") is not None and not isinstance(data["created_at"], datetime):
                    data["created_at"] = datetime.fromisoformat(str(data["created_at"]))
                rule = AutomationRule(
                    **{key: data[key] for key in AutomationRule.__dataclass_fields__ if key in data}
                )
                self.rules[rule.id] = rule
            except (KeyError, TypeError, ValueError):
                continue

    def create(self, owner, pet_id, trigger, action):
        with self.lock:
            if not trigger or not action or action.get("kind") in {"DIAGNOSE", "PRESCRIBE", "MEDICAL_ESCALATION"}: raise ValueError("AUTOMATION_ACTION_NOT_ALLOWED")
            rule = AutomationRule(owner, pet_id, trigger, action)
            self.rules[rule.id] = rule
            self._save(rule)
            return rule

    def _save(self, rule: AutomationRule) -> None:
        if self.store and hasattr(self.store, "put"):
            self.store.put("automation_rules", rule)

    def evaluate(self, owner, pet_id, event: dict, evaluation_key: str) -> list[dict]:
        with self.lock:
            fired = []
            for rule in self.rules.values():
                if rule.owner_user_id == owner and rule.pet_id == pet_id and rule.enabled and rule.last_fired_key != evaluation_key and self._matches(rule.trigger, event):
                    rule.last_fired_key = evaluation_key
                    self._save(rule)
                    fired.append({"rule_id": rule.id, "action": rule.action, "reason": "DETERMINISTIC_RULE_MATCH"})
            return fired

    @staticmethod
    def _matches(trigger, event):
        return all(event.get(k) == v for k, v in trigger.items())
