from datetime import UTC, datetime

from app.repositories.agents.memory import MemoryAgentRepository


def test_memory_repository_claim_and_fence():
    repo = MemoryAgentRepository()
    repo.create_run_with_initial_step({"id": "r", "owner_user_id": "u"}, {"id": "s", "status": "READY"})
    now = datetime.now(UTC)
    assert repo.claim_step("r", "s", "w1", now)
    assert not repo.claim_step("r", "s", "w2", now)
    assert not repo.commit_step_result("r", "s", "w2", 1, {"x": 1})
    assert repo.commit_step_result("r", "s", "w1", 1, {"x": 1})


def test_memory_repository_can_schedule_retry_and_reclaim():
    repo = MemoryAgentRepository()
    repo.create_run_with_initial_step({"id": "r", "owner_user_id": "u"}, {"id": "s", "status": "READY"})
    now = datetime.now(UTC)
    assert repo.claim_step("r", "s", "w1", now)
    assert repo.schedule_step_retry("r", "s", "w1", 1, now)
    assert repo.claim_step("r", "s", "w2", now)
    assert not repo.schedule_step_retry("r", "s", "w1", 1, now)
