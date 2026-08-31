from app.agents.contracts import AgentOrchestrator
from app.repositories.agents.memory import MemoryAgentRepository


def test_orchestrator_writes_initial_work_item_through_repository():
    repo = MemoryAgentRepository()
    run = AgentOrchestrator(repository=repo).create_run("owner", "check", "dog")
    assert repo.get_run_owned(run.id, "owner")["id"] == run.id
    assert repo.list_steps(run.id)[0]["status"] == "READY"
