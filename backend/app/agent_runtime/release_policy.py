from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPolicy:
    policy_id: str = "model-policy-v1"
    provider: str = "GEMINI_BACKEND_ONLY"
    model: str = "configured-server-model"
    prompt_version: str = "1.0.0"
    schema_version: str = "1.0.0"
    safety_policy_version: str = "1.0.0"
    web_enabled: bool = False
    local_model_enabled: bool = False


def validate_policy(policy: ModelPolicy):
    if policy.web_enabled or policy.local_model_enabled: raise ValueError("AGENT_MODEL_POLICY_NOT_ALLOWED")
    if not all((policy.provider, policy.model, policy.prompt_version, policy.schema_version, policy.safety_policy_version)): raise ValueError("AGENT_MODEL_POLICY_INCOMPLETE")
    return policy
