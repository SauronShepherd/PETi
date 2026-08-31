"""Allow-listed agent recipes for the bounded PETi runtime.

Recipes are data, not model instructions: the coordinator can only select a
recipe whose inputs and executors are explicitly released by PETi.
"""
from dataclasses import dataclass

from app.agents.technical_contracts import ExecutionPlan, PlanNode


@dataclass(frozen=True)
class Recipe:
    recipe_id: str
    subject_domain: str
    required_context: tuple[str, ...]
    nodes: tuple[tuple[str, str, str, tuple[str, ...]], ...]

    def build(self, run_id: str) -> ExecutionPlan:
        return ExecutionPlan(
            run_id=run_id,
            recipe_id=self.recipe_id,
            nodes=[PlanNode(node, kind, executor, list(deps), "1.0.0") for node, kind, executor, deps in self.nodes],
            expected_final_output_schema="agent-answer-v1",
        )


FECES_COMPARE_V1 = Recipe(
    recipe_id="FECES_COMPARE_V1",
    subject_domain="FECES",
    required_context=("RECENT_FECES_OBSERVATIONS",),
    nodes=(
        ("goal-resolve", "AGENT", "GOAL_RESOLUTION", ()),
        ("evidence-intake", "AGENT", "EVIDENCE_INTAKE", ("goal-resolve",)),
        ("feces-current", "AGENT", "FECES_CURRENT_ASSESSMENT", ("evidence-intake",)),
        ("longitudinal", "AGENT", "FECES_LONGITUDINAL_COMPARE", ("feces-current",)),
        ("final-safety", "VALIDATOR", "FINAL_SYNTHESIS", ("longitudinal",)),
        ("synthesis", "AGENT", "FINAL_SYNTHESIS", ("final-safety",)),
    ),
)


RECIPES = {FECES_COMPARE_V1.recipe_id: FECES_COMPARE_V1}

FECES_CURRENT_V1 = Recipe(
    "FECES_CURRENT_V1", "FECES", (),
    (("goal-resolve", "AGENT", "GOAL_RESOLUTION", ()),
     ("evidence-intake", "AGENT", "EVIDENCE_INTAKE", ("goal-resolve",)),
     ("feces-current", "AGENT", "FECES_CURRENT_ASSESSMENT", ("evidence-intake",)),
     ("final-safety", "VALIDATOR", "FINAL_SYNTHESIS", ("feces-current",)),
     ("synthesis", "AGENT", "FINAL_SYNTHESIS", ("final-safety",))),
)
FECES_COMPARE_FOLLOW_UP_V1 = Recipe(
    "FECES_COMPARE_FOLLOW_UP_V1", "FECES", ("RECENT_FECES_OBSERVATIONS",),
    FECES_COMPARE_V1.nodes[:-1] + (("care-proposal", "AGENT", "CARE_FOLLOW_UP_PROPOSAL", ("final-safety",)),
                              ("user-approval", "USER_APPROVAL", "CARE_FOLLOW_UP_PROPOSAL", ("care-proposal",)),
                              ("execute-reminder", "TOOL", "CREATE_CARE_REMINDER_ACTION", ("user-approval",))),
)
RECIPES.update({x.recipe_id: x for x in (FECES_CURRENT_V1, FECES_COMPARE_FOLLOW_UP_V1)})


def resolve_recipe(recipe_id: str) -> Recipe:
    try:
        return RECIPES[recipe_id]
    except KeyError as exc:
        raise ValueError("AGENT_RECIPE_NOT_RELEASED") from exc
