"""Durable-DAG coordination primitives used by private workers."""
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from .plan_validator import PlanValidator


@dataclass(frozen=True)
class CoordinatorResult:
    completed: tuple[str, ...]
    waiting: tuple[str, ...]
    failed: tuple[str, ...]


class RunCoordinator:
    def __init__(self, *, validator: PlanValidator, dispatcher, max_steps: int = 8, budget=None):
        self.validator, self.dispatcher, self.max_steps = validator, dispatcher, max_steps
        self.budget = budget or {}

    def dispatch_by_kind(self, node, outputs, handlers):
        kind = node.get("kind")
        if kind not in {"AGENT", "TOOL", "FUNCTION", "USER_INPUT", "USER_APPROVAL", "VALIDATOR"}:
            raise ValueError("AGENT_PLAN_NODE_KIND_INVALID")
        handler = handlers.get(kind)
        if handler is None:
            raise ValueError("AGENT_NODE_HANDLER_UNAVAILABLE")
        return handler(node, outputs)

    def run(self, nodes, outputs=None):
        outputs = dict(outputs or {})
        self.validator.validate(nodes, max_steps=self.max_steps, requires_final_safety=False)
        remaining = {n["node_id"]: n for n in nodes}
        completed, waiting, failed = [], [], []
        exhausted = False
        while remaining:
            ready = [n for n in remaining.values() if all(dep in outputs for dep in n.get("depends_on", []))]
            if not ready:
                waiting.extend(sorted(remaining)); break
            for node in ready:
                if len(completed) >= self.budget.get("max_agent_steps", self.max_steps):
                    exhausted = True
                    waiting.extend(sorted(remaining))
                    remaining.clear()
                    break
                try:
                    result = self.dispatcher(node, outputs)
                except (RuntimeError, ValueError):
                    failed.append(node["node_id"]); remaining.pop(node["node_id"]); continue
                if result is None or (isinstance(result, dict) and result.get("waiting")):
                    waiting.append(node["node_id"]); remaining.pop(node["node_id"]); continue
                outputs[node["node_id"]] = result; completed.append(node["node_id"]); remaining.pop(node["node_id"])
        if exhausted:
            failed.append("AGENT_BUDGET_EXHAUSTED")
        return CoordinatorResult(tuple(completed), tuple(waiting), tuple(failed))

    def run_durable(self, *, run_id, nodes, repository, now=None, worker_id=None, outputs=None):
        """Execute ready DAG nodes through repository step leases.

        The repository is the authority for cross-instance ownership. A worker
        that loses a lease never commits a result, so task redelivery cannot
        create a second durable step effect.
        """
        outputs = dict(outputs or {})
        self.validator.validate(nodes, max_steps=self.max_steps, requires_final_safety=False)
        now = now or datetime.now(UTC)
        worker_id = worker_id or str(uuid4())
        remaining = {n["node_id"]: n for n in nodes}
        completed, waiting, failed = [], [], []
        while remaining:
            ready = [n for n in remaining.values() if all(dep in outputs for dep in n.get("depends_on", []))]
            if not ready:
                waiting.extend(sorted(remaining)); break
            for node in ready:
                node_id = node["node_id"]
                if len(completed) >= self.budget.get("max_agent_steps", self.max_steps):
                    waiting.extend(sorted(remaining)); remaining.clear(); break
                if not repository.claim_step(run_id, node_id, worker_id, now):
                    waiting.append(node_id); remaining.pop(node_id); continue
                steps = repository.list_steps(run_id)
                leased = next((step for step in steps if step.get("id", step.get("step_id")) == node_id), None)
                epoch = int((leased or {}).get("lease_epoch", 0))
                try:
                    result = self.dispatcher(node, outputs)
                    if result is None or (isinstance(result, dict) and result.get("waiting")):
                        waiting.append(node_id); remaining.pop(node_id); continue
                    if not repository.commit_step_result(run_id, node_id, worker_id, epoch, result):
                        waiting.append(node_id); remaining.pop(node_id); continue
                    outputs[node_id] = result; completed.append(node_id); remaining.pop(node_id)
                except (RuntimeError, ValueError) as exc:
                    retryable = bool(getattr(exc, "retryable", False))
                    if retryable and hasattr(repository, "schedule_step_retry"):
                        repository.schedule_step_retry(run_id, node_id, worker_id, epoch, now)
                        waiting.append(node_id)
                    else:
                        failed.append(node_id)
                    remaining.pop(node_id)
        return CoordinatorResult(tuple(completed), tuple(waiting), tuple(failed))
