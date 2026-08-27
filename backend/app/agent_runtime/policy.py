from dataclasses import dataclass


@dataclass(frozen=True)
class RunBudget:
    max_agent_steps: int = 8
    max_model_calls: int = 3
    max_tool_calls: int = 12
    max_repair_attempts: int = 1
    max_media_bytes: int = 20_000_000
    max_context_items: int = 50
    max_wall_clock_seconds: int = 120
    max_estimated_cost_microunits: int = 100


class BudgetGuard:
    def __init__(self, budget: RunBudget | None = None): self.budget = budget or RunBudget(); self.counts = {"agent_steps": 0, "model_calls": 0, "tool_calls": 0, "repair_attempts": 0, "media_bytes": 0, "context_items": 0}

    def consume(self, kind: str, amount: int = 1):
        if kind not in self.counts: raise ValueError("AGENT_BUDGET_DIMENSION_INVALID")
        self.counts[kind] += amount
        limits = {"agent_steps": self.budget.max_agent_steps, "model_calls": self.budget.max_model_calls, "tool_calls": self.budget.max_tool_calls, "repair_attempts": self.budget.max_repair_attempts, "media_bytes": self.budget.max_media_bytes, "context_items": self.budget.max_context_items}
        if self.counts[kind] > limits[kind]: raise ValueError("AGENT_BUDGET_EXCEEDED")
