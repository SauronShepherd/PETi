from app.agent_runtime.adk_graph import build_peti_agent, graph_metadata


def test_peti_declares_a_google_adk_multi_agent_graph():
    metadata = graph_metadata("gemini-3.5-flash")
    assert metadata["framework"] == "google-adk"
    assert metadata["root_agent"] == "peti_orchestrator_agent"
    assert len(metadata["sub_agents"]) >= 3


def test_peti_builds_the_adk_root_and_three_delegated_agents():
    root = build_peti_agent("gemini-3.5-flash")
    assert root.name == "peti_orchestrator_agent"
    assert {agent.name for agent in root.sub_agents} == {
        "evidence_intake_agent",
        "pet_specialist_agent",
        "safety_review_agent",
    }
