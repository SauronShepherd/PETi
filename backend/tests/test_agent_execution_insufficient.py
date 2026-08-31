from typing import ClassVar

from app.agent_runtime.agent_model_provider import ProviderInvocationResult
from app.agent_runtime.execution import AgentExecutionService
from app.agents.contracts import AgentOrchestrator
from app.ai.providers.fake import FakeAIProvider


class Media:
    items: ClassVar = [{"id": "current", "pet_id": "pet-a"}]


class Provider:
    def __init__(self): self.roles = []
    def invoke(self, **kwargs):
        self.roles.append(kwargs["role"])
        payload = {"usable": True, "evidence_quality": "GOOD"} if kwargs["role"] == "EVIDENCE_INTAKE" else {"evidence_quality": "GOOD", "observations": []}
        return ProviderInvocationResult("test", "stable", "req", payload, {})


def test_compare_without_compatible_history_skips_longitudinal_model():
    provider = Provider()
    runs = AgentOrchestrator()
    run = runs.create_run("owner-a", "compare today's stool with history", "pet-a")
    result = AgentExecutionService(runs, FakeAIProvider(), agent_model_provider=provider).execute("owner-a", run.id, Media())
    assert result["state"] == "COMPLETED"
    assert provider.roles == ["EVIDENCE_INTAKE", "FECES_CURRENT_ASSESSMENT"]
