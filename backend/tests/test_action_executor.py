from datetime import UTC, datetime

import pytest
from app.agent_runtime.action_executor import CareActionExecutor


class Pets:
    def get(self, owner, pet_id):
        return object()


class Care:
    def __init__(self):
        self.calls = []

    def create_care(self, owner, pet_id, payload, key, pets):
        self.calls.append((owner, pet_id, payload, key))
        return type("Record", (), {"id": "care-1"})()


def test_executor_normalizes_iso_due_at_and_is_repeatable_by_key():
    care = Care()
    executor = CareActionExecutor(care, Pets())
    action = {"id": "action-1", "action_type": "CARE_REMINDER", "summary": "Check tomorrow", "arguments": {"due_at": "2030-01-02T09:00:00Z"}}
    result = executor.execute("owner-1", "dog-1", action, "agent-action-1")
    assert result["status"] == "EXECUTED"
    assert care.calls[0][2]["due_at"] == datetime(2030, 1, 2, 9, tzinfo=UTC)
    assert executor.execute("owner-1", "dog-1", action, "agent-action-1") == result
    assert len(care.calls) == 1


def test_executor_rejects_invalid_due_at_before_mutation():
    care = Care()
    executor = CareActionExecutor(care, Pets())
    with pytest.raises(ValueError, match="AGENT_REMINDER_DUE_AT_INVALID"):
        executor.execute("owner-1", "dog-1", {"id": "a", "action_type": "CARE_REMINDER", "arguments": {"due_at": "tomorrow"}}, "k")
    assert care.calls == []
