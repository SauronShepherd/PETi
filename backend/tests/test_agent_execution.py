from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Barrier

from app.agent_runtime.execution import AgentExecutionService
from app.agents.contracts import AgentOrchestrator, RunState
from app.ai.providers.fake import FakeAIProvider


@dataclass
class Media:
    items: list | None = None

    def __post_init__(self):
        self.items = self.items or []


def test_agent_execution_persists_bounded_plan_and_review_state():
    runs = AgentOrchestrator()
    service = AgentExecutionService(runs, FakeAIProvider())
    run = runs.create_run("owner-a", "What should I review?", "pet-a")
    result = service.execute("owner-a", run.id, Media())
    assert result["state"] == RunState.COMPLETED
    assert [step["step_id"] for step in result["steps"][:5]] == ["plan", "evidence-intake", "peti-check", "safety-review", "care-report"]
    assert result["steps"][-1]["final"]["status"] == "REVIEW_REQUIRED"


def test_agent_duplicate_delivery_uses_one_provider_call():
    class CountingProvider(FakeAIProvider):
        def __init__(self):
            super().__init__()
            self.calls = 0

        def analyze(self, media, prompt="", user_context=None):
            self.calls += 1
            return super().analyze(media, prompt, user_context)

    provider = CountingProvider()
    runs = AgentOrchestrator()
    service = AgentExecutionService(runs, provider)
    run = runs.create_run("owner-a", "What should I review?", "pet-a")
    barrier = Barrier(2)

    def execute():
        barrier.wait()
        return service.execute("owner-a", run.id, Media())

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: execute(), range(2)))

    assert provider.calls == 1
    assert all(item["state"] == RunState.COMPLETED for item in results)


def test_agent_unexpected_provider_failure_persists_failed_state():
    class BrokenProvider(FakeAIProvider):
        def analyze(self, media, prompt="", user_context=None):
            raise RuntimeError("unexpected provider failure")

    runs = AgentOrchestrator()
    service = AgentExecutionService(runs, BrokenProvider())
    run = runs.create_run("owner-a", "What should I review?", "pet-a")

    try:
        service.execute("owner-a", run.id, Media())
    except RuntimeError as exc:
        assert str(exc) == "unexpected provider failure"
    else:
        raise AssertionError("expected provider failure")

    assert runs.get("owner-a", run.id).state == RunState.FAILED


def test_agent_run_lookup_can_reload_a_persisted_run():
    class Snapshot:
        exists = True
        def to_dict(self):
            return {"id": "run-b", "owner_user_id": "owner-b", "pet_id": "pet-b", "goal": "review", "state": "QUEUED", "steps": [], "evidence": [], "policy_snapshot": {}}

    class Document:
        def get(self): return Snapshot()

    class Collection:
        def document(self, _): return Document()

    class Store:
        client = type("Client", (), {"collection": lambda _, name: Collection()})()

    runs = AgentOrchestrator(store=Store())
    assert runs.get("owner-b", "run-b").state == RunState.QUEUED


def test_agent_orchestrator_hydrates_serialized_lifecycle_timestamps():
    class Store:
        def __init__(self):
            self.rows = {"agent_sessions": [], "agent_runs": [], "agent_context_requests": [], "agent_actions": []}

        def all(self, collection):
            return list(self.rows[collection])

        def put_raw(self, collection, key, data):
            self.rows[collection] = [row for row in self.rows[collection] if row.get("id") != key]
            self.rows[collection].append(dict(data))

    store = Store()
    first = AgentOrchestrator(store=store)
    session = first.create_session("owner-a", "pet-a")
    run = first.create_run("owner-a", "review", "pet-a", session_id=session.id)
    fixed = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
    store.rows["agent_sessions"][0]["created_at"] = fixed.isoformat()
    store.rows["agent_sessions"][0]["updated_at"] = fixed.isoformat()
    store.rows["agent_runs"][0]["created_at"] = fixed.isoformat()
    store.rows["agent_runs"][0]["updated_at"] = fixed.isoformat()

    restarted = AgentOrchestrator(store=store)
    assert restarted.sessions[session.id].created_at == fixed
    assert restarted.runs[run.id].updated_at == fixed


def test_agent_state_transition_uses_injected_clock():
    fixed = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
    runs = AgentOrchestrator(clock=lambda: fixed)
    run = runs.create_run("owner-a", "review", "pet-a")
    assert run.updated_at == fixed
