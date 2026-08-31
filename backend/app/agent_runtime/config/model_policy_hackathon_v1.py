from app.agent_runtime.release_policy import ModelPolicy

HACKATHON_MODEL_POLICY_V1 = ModelPolicy(
    policy_id="model-policy-hackathon-v1",
    provider="GEMINI_BACKEND_ONLY",
    model="gemini-2.5-flash",
    prompt_version="1.0.0",
    schema_version="1.0.0",
    safety_policy_version="1.0.0",
)
