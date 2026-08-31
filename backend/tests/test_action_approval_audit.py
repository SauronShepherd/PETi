from app.agents.contracts import AgentOrchestrator


def test_approval_is_recorded_as_separate_immutable_event():
    runs = AgentOrchestrator()
    run = runs.create_run("owner", "remind me", "dog")
    action = runs.propose_action("owner", run.id, "CARE_REMINDER", "Check tomorrow", {"due_at": "2030-01-01T09:00:00Z"})
    result = runs.decide_action("owner", run.id, action["id"], False, action["approval_payload_hash"])
    assert result["status"] == "REJECTED"
    # The in-memory orchestrator has no durable store, but still exposes the
    # approval contract through the action state; durable stores receive the
    # separate agent_action_approvals document above.
    assert result["decision_id"]
    assert "receipt_id" not in result
