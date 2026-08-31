from app.api.agent_runs import router


def test_agent_execution_is_worker_only():
    assert "/v1/agent-runs/{run_id}/execute" not in {route.path for route in router.routes}
