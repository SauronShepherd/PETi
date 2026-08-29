from app.agent_runtime.adk_graph import graph_metadata


def test_peti_declares_a_google_adk_multi_agent_graph():
    metadata = graph_metadata("gemini-3.5-flash")
    assert metadata["framework"] == "google-adk"
    assert metadata["root_agent"] == "peti_orchestrator_agent"
    assert len(metadata["sub_agents"]) >= 3
