from app.agent_runtime.capability_registry import CapabilityRegistry
from app.agent_runtime.config.capabilities_v1 import CAPABILITIES_V1
from app.agent_runtime.plan_validator import PlanValidator
from app.agent_runtime.recipe_registry import FECES_COMPARE_V1, resolve_recipe


def test_feces_compare_recipe_is_bounded_and_ordered():
    plan = FECES_COMPARE_V1.build("run-1")
    assert [node.executor_id for node in plan.nodes] == [
        "GOAL_RESOLUTION", "EVIDENCE_INTAKE", "FECES_CURRENT_ASSESSMENT",
        "FECES_LONGITUDINAL_COMPARE", "FINAL_SYNTHESIS", "FINAL_SYNTHESIS",
    ]
    assert plan.nodes[3].depends_on == ["feces-current"]


def test_unknown_recipe_is_closed_by_default():
    try:
        resolve_recipe("arbitrary-model-selected-recipe")
    except ValueError as exc:
        assert str(exc) == "AGENT_RECIPE_NOT_RELEASED"
    else:
        raise AssertionError("unreleased recipe was accepted")


def test_follow_up_recipe_has_no_orphaned_dependencies():
    plan = resolve_recipe("FECES_COMPARE_FOLLOW_UP_V1").build("run-2")
    PlanValidator(CapabilityRegistry(CAPABILITIES_V1)).validate(
        [{"node_id": n.node_id, "executor_id": n.executor_id, "depends_on": n.depends_on} for n in plan.nodes],
        requires_final_safety=False,
        max_steps=12,
    )
