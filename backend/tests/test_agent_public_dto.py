from app.agents.contracts import AgentOrchestrator
from app.api.models.agent_public import project_run


def test_public_projection_redacts_internal_run_fields():
    run = AgentOrchestrator().create_run("owner", "check", "dog")
    run.policy_snapshot = {"secret": "must not leak"}
    public = project_run(run).model_dump()
    assert public["run_id"] == run.id
    assert "policy_snapshot" not in public
    assert "owner_user_id" not in public
    assert "secret" not in str(public)
