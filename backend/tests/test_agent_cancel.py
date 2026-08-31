from app.agents.contracts import AgentOrchestrator, RunState
from app.repositories.agents.memory import MemoryAgentRepository


def test_cancel_is_a_legal_terminal_transition():
    runs = AgentOrchestrator()
    run = runs.create_run("owner", "check", "dog")
    canceled = runs.cancel("owner", run.id)
    assert canceled.state is RunState.CANCELLED


def test_cancel_marks_durable_steps_unclaimable():
    repository = MemoryAgentRepository()
    runs = AgentOrchestrator(repository=repository)
    run = runs.create_run("owner", "review", "pet")
    repository.ensure_steps(run.id, [{"id": "next"}])
    assert runs.cancel("owner", run.id).state is RunState.CANCELLED
    assert not repository.claim_step(run.id, "next", "worker", runs.clock())
