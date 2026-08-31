import pytest
from app.agent_runtime.capability_registry import CapabilityRegistry
from app.agent_runtime.config.capabilities_v1 import CAPABILITIES_V1
from app.agent_runtime.fast_path import FastPathResolver
from app.agent_runtime.plan_validator import PlanValidator
from app.agent_runtime.recipe_registry import FECES_COMPARE_FOLLOW_UP_V1, resolve_recipe


def test_fast_path_is_strict_and_model_free():
    assert FastPathResolver().resolve("show next reminder").requires_model is False
    assert FastPathResolver().resolve("is my dog sick?") is None


def test_follow_up_recipe_is_allowlisted():
    assert resolve_recipe("FECES_COMPARE_FOLLOW_UP_V1") is FECES_COMPARE_FOLLOW_UP_V1


def test_plan_validator_rejects_cycles():
    validator = PlanValidator(CapabilityRegistry(CAPABILITIES_V1))
    with pytest.raises(ValueError, match="AGENT_PLAN_CYCLE"):
        validator.validate([
            {"node_id": "a", "executor_id": "EVIDENCE_INTAKE", "depends_on": ["b"]},
            {"node_id": "b", "executor_id": "FECES_CURRENT_ASSESSMENT", "depends_on": ["a"]},
        ], requires_final_safety=False)
