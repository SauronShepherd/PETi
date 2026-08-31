import pytest
from app.agents.contracts import AgentOrchestrator


def test_rejected_action_advances_run_through_versioned_mutation():
    runs = AgentOrchestrator()
    run = runs.create_run("owner", "remind", "dog")
    action = runs.propose_action("owner", run.id, "CARE_REMINDER", "Check", {"due_at": "2030-01-01T09:00:00Z"})
    result = runs.decide_action("owner", run.id, action["id"], False, action["approval_payload_hash"])
    assert result["status"] == "REJECTED"


def test_expired_action_cannot_be_approved():
    from datetime import UTC, datetime, timedelta
    now = datetime(2030, 1, 1, tzinfo=UTC)
    runs = AgentOrchestrator(clock=lambda: now)
    run = runs.create_run("owner", "remind", "dog")
    action = runs.propose_action("owner", run.id, "CARE_REMINDER", "Check", {"due_at": "2030-01-02T09:00:00Z"})
    action["expires_at"] = now - timedelta(seconds=1)
    runs.actions[action["id"]] = action
    with pytest.raises(ValueError, match="AGENT_ACTION_EXPIRED"):
        runs.decide_action("owner", run.id, action["id"], True, action["approval_payload_hash"])
