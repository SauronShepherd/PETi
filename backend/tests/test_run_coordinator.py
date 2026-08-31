from app.agent_runtime.capability_registry import CapabilityRegistry
from app.agent_runtime.config.capabilities_v1 import CAPABILITIES_V1
from app.agent_runtime.coordinator import RunCoordinator
from app.agent_runtime.plan_validator import PlanValidator
from app.repositories.agents.memory import MemoryAgentRepository


def test_coordinator_dispatches_dag_in_dependency_order():
    seen = []
    def dispatch(node, outputs):
        seen.append(node["node_id"]); return {"ok": True}
    nodes = [
        {"node_id": "a", "kind": "AGENT", "executor_id": "GOAL_RESOLUTION"},
        {"node_id": "b", "kind": "AGENT", "executor_id": "EVIDENCE_INTAKE", "depends_on": ["a"]},
    ]
    result = RunCoordinator(validator=PlanValidator(CapabilityRegistry(CAPABILITIES_V1)), dispatcher=dispatch).run(nodes)
    assert seen == ["a", "b"] and result.failed == ()

def test_coordinator_does_not_dispatch_after_step_budget():
    seen = []
    nodes = [{"node_id": x, "kind": "AGENT", "executor_id": "GOAL_RESOLUTION"} for x in ("a", "b")]
    result = RunCoordinator(validator=PlanValidator(CapabilityRegistry(CAPABILITIES_V1)), dispatcher=lambda n, o: seen.append(n["node_id"]) or {"ok": True}, budget={"max_agent_steps": 1}).run(nodes)
    assert seen == ["a"]
    assert "AGENT_BUDGET_EXHAUSTED" in result.failed

def test_dispatch_by_kind_requires_explicit_handler():
    coordinator = RunCoordinator(validator=PlanValidator(CapabilityRegistry(CAPABILITIES_V1)), dispatcher=lambda *_: None)
    assert coordinator.dispatch_by_kind({"kind": "TOOL"}, {}, {"TOOL": lambda *_: {"ok": True}})["ok"]
    try:
        coordinator.dispatch_by_kind({"kind": "MODEL"}, {}, {})
    except ValueError as exc:
        assert str(exc) == "AGENT_PLAN_NODE_KIND_INVALID"
    else:
        raise AssertionError("unknown node kind accepted")

def test_durable_coordinator_claims_and_commits_each_step_once():
    repository = MemoryAgentRepository()
    repository.create_run_with_initial_step({"id": "run-1", "owner_user_id": "owner"}, {"id": "a", "run_id": "run-1", "status": "READY"})
    repository.steps[("run-1", "b")] = {"id": "b", "run_id": "run-1", "status": "READY"}
    nodes = [
        {"node_id": "a", "kind": "AGENT", "executor_id": "GOAL_RESOLUTION"},
        {"node_id": "b", "kind": "AGENT", "executor_id": "EVIDENCE_INTAKE", "depends_on": ["a"]},
    ]
    seen = []
    coordinator = RunCoordinator(validator=PlanValidator(CapabilityRegistry(CAPABILITIES_V1)), dispatcher=lambda n, o: seen.append(n["node_id"]) or {"ok": True})
    result = coordinator.run_durable(run_id="run-1", nodes=nodes, repository=repository, worker_id="worker-1")
    assert result.completed == ("a", "b")
    assert seen == ["a", "b"]
    assert all(step["status"] == "SUCCEEDED" for step in repository.list_steps("run-1"))


def test_durable_coordinator_requeues_retryable_step():
    repository = MemoryAgentRepository()
    repository.create_run_with_initial_step({"id": "run-2", "owner_user_id": "owner"}, {"id": "a", "run_id": "run-2", "status": "READY"})
    class Retryable(RuntimeError):
        retryable = True
    coordinator = RunCoordinator(validator=PlanValidator(CapabilityRegistry(CAPABILITIES_V1)), dispatcher=lambda *_: (_ for _ in ()).throw(Retryable()))
    result = coordinator.run_durable(run_id="run-2", nodes=[{"node_id": "a", "kind": "AGENT", "executor_id": "GOAL_RESOLUTION"}], repository=repository, worker_id="worker")
    assert result.waiting == ("a",) and repository.list_steps("run-2")[0]["status"] == "RETRY_SCHEDULED"
