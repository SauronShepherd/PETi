from app.agents.contracts import AgentOrchestrator, RunState


def test_context_response_resumes_run_and_is_owner_scoped():
    runs = AgentOrchestrator()
    run = runs.create_run("owner", "need context", "dog")
    request = runs.request_context("owner", run.id, "HISTORY", ["recent observations"])
    response = runs.respond_context("owner", run.id, request["id"], ["care-1"])
    assert response["status"] == "RESPONDED"
    assert runs.get("owner", run.id).state is RunState.RUNNING
