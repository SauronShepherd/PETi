from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict

import pytest
from app.automation.rules import RuleEngine


class MemoryStore:
    def __init__(self):
        self.rows: dict[str, dict] = {}

    def all(self, collection: str):
        return list(self.rows.values()) if collection == "automation_rules" else []

    def put(self, collection: str, rule):
        self.rows[rule.id] = asdict(rule)


def test_rule_and_idempotency_marker_survive_restart():
    store = MemoryStore()
    first = RuleEngine(store=store)
    rule = first.create("owner-1", "pet-1", {"event": "VACCINATION_DUE"}, {"kind": "NOTIFY"})
    event = {"event": "VACCINATION_DUE"}

    assert len(first.evaluate("owner-1", "pet-1", event, "event-1")) == 1
    restarted = RuleEngine(store=store)
    assert restarted.evaluate("owner-1", "pet-1", event, "event-1") == []
    assert len(restarted.evaluate("owner-1", "pet-1", event, "event-2")) == 1
    assert restarted.rules[rule.id].last_fired_key == "event-2"


def test_rule_creation_rejects_clinical_actions_before_persistence():
    store = MemoryStore()
    engine = RuleEngine(store=store)
    with pytest.raises(ValueError, match="AUTOMATION_ACTION_NOT_ALLOWED"):
        engine.create("owner-1", "pet-1", {"event": "X"}, {"kind": "DIAGNOSE"})
    assert store.rows == {}


def test_concurrent_rule_evaluation_emits_one_action():
    engine = RuleEngine()
    engine.create("owner-1", "pet-1", {"event": "X"}, {"kind": "NOTIFY"})
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: engine.evaluate("owner-1", "pet-1", {"event": "X"}, "event-1"), range(8)))
    assert sum(len(result) for result in results) == 1
