from app.agents.role_agents import ROLE_AGENTS, get_role_agent


def test_all_released_roles_have_capability_specific_instructions():
    assert {"EVIDENCE_INTAKE", "FECES_CURRENT_ASSESSMENT", "FECES_LONGITUDINAL_COMPARE", "CARE_FOLLOW_UP_PROPOSAL", "FINAL_SYNTHESIS"} <= ROLE_AGENTS.keys()
    assert all(agent.instruction for agent in ROLE_AGENTS.values())
    assert get_role_agent("FECES_CURRENT_ASSESSMENT").name == "feces_specialist"
