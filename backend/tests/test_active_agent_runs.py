from app.agents.contracts import AgentOrchestrator


def test_active_runs_are_scoped_to_owner_and_dog():
    runs = AgentOrchestrator()
    first = runs.create_run("u", "review", "dog-1")
    runs.create_run("u", "review", "dog-2")
    runs.create_run("other", "review", "dog-1")
    assert [run.id for run in runs.list_active_runs("u", "dog-1")] == [first.id]
