from app.agent_runtime.agent_model_provider import ProviderInvocationResult
from app.agent_runtime.role_dispatch import RoleDispatcher, RoleInvocation
from app.agents.schemas import EvidenceIntakeResultV1, FecesAgentResultV1


class Provider:
    def __init__(self):
        self.calls = []

    def invoke(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs["role"] == "EVIDENCE_INTAKE":
            payload = {"usable": True, "evidence_quality": "GOOD"}
        else:
            payload = {"evidence_quality": "GOOD", "observations": []}
        return ProviderInvocationResult("test", "stable-model", "req", payload, {"input": 1})


def test_compare_subgraph_requires_distinct_role_invocations_and_schemas():
    provider = Provider()
    dispatcher = RoleDispatcher(provider)
    context = {"owner_user_id": "u", "pet_id": "p", "items": []}
    results = dispatcher.dispatch_many([
        RoleInvocation("EVIDENCE_INTAKE", "binding", "prompt-v1", context, EvidenceIntakeResultV1),
        RoleInvocation("FECES_CURRENT_ASSESSMENT", "binding", "prompt-v1", context, FecesAgentResultV1),
    ])
    assert len(results) == 2
    assert [call["role"] for call in provider.calls] == ["EVIDENCE_INTAKE", "FECES_CURRENT_ASSESSMENT"]
    assert provider.calls[0]["context_bundle"] is context
    assert provider.calls[1]["response_schema"] is FecesAgentResultV1
