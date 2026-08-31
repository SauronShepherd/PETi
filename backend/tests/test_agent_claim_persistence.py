from app.agents.contracts import AgentOrchestrator


class Store:
    def __init__(self):
        self.rows = {"agent_runs": [], "agent_claims": []}

    def all(self, collection):
        return list(self.rows.get(collection, []))

    def put_raw(self, collection, key, data):
        rows = self.rows.setdefault(collection, [])
        rows[:] = [row for row in rows if row.get("id") != key]
        rows.append({**dict(data), "id": key})


def test_claims_are_recoverable_after_orchestrator_restart():
    store = Store()
    first = AgentOrchestrator(store=store)
    run = first.create_run("owner-a", "review", "pet-a")
    first.persist_claims("owner-a", run.id, [{"text": "visible", "evidence_ids": ["asset-1"]}])
    second = AgentOrchestrator(store=store)
    assert second.list_claims("owner-a", run.id)[0]["text"] == "visible"
    assert second.list_claims("owner-b", run.id) == []
