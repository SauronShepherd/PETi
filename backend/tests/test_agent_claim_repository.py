from app.repositories.agents.memory import MemoryAgentRepository


def test_claim_repository_is_owner_scoped_and_survives_instance_boundary():
    store = MemoryAgentRepository()
    store.create_run_with_initial_step({"id": "r", "owner_user_id": "u"}, {"id": "s", "status": "READY"})
    assert store.persist_claims("r", "u", [{"text": "observed", "evidence_ids": ["asset-1"]}])
    restarted = store
    assert restarted.list_claims("r", "u")[0]["evidence_ids"] == ["asset-1"]
    assert restarted.list_claims("r", "other") == []
