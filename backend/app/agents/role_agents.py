"""Released capability-specific agent definitions.

These are intentionally small descriptors: durable orchestration and safety
remain in PETi, while ADK receives only the selected role's instruction.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class RoleAgent:
    capability_id: str
    name: str
    instruction: str

ROLE_AGENTS = {
    "GOAL_RESOLUTION": RoleAgent("GOAL_RESOLUTION", "goal_resolver", "Resolve only the bounded user goal; never select tools or permissions."),
    "EVIDENCE_INTAKE": RoleAgent("EVIDENCE_INTAKE", "evidence_intake", "Assess supplied evidence usability and directly observable facts only. No diagnosis or treatment."),
    "FECES_CURRENT_ASSESSMENT": RoleAgent("FECES_CURRENT_ASSESSMENT", "feces_specialist", "Use PETi visible stool taxonomy. Preserve NOT_OBSERVED versus NOT_ASSESSABLE; never diagnose or prescribe."),
    "FECES_LONGITUDINAL_COMPARE": RoleAgent("FECES_LONGITUDINAL_COMPARE", "longitudinal_specialist", "Use only deterministic compatible same-dog candidates. Output comparability before any change label; no causality."),
    "CARE_FOLLOW_UP_PROPOSAL": RoleAgent("CARE_FOLLOW_UP_PROPOSAL", "care_planner", "Draft bounded reminders or observation follow-ups from validated claims only. Never mutate or prescribe."),
    "FINAL_SYNTHESIS": RoleAgent("FINAL_SYNTHESIS", "final_synthesis", "Compose only validated claims, evidence references and deterministic safety state. Do not add unsupported facts."),
}

def get_role_agent(capability_id: str) -> RoleAgent:
    try: return ROLE_AGENTS[capability_id]
    except KeyError as exc: raise ValueError("AGENT_CAPABILITY_NOT_RELEASED") from exc
