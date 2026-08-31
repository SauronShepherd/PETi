from app.agent_runtime.context_broker import ContextBroker
from app.agent_runtime.context_sources import CurrentMediaContextSource, PetProfileContextSource


def test_typed_sources_scope_rows_before_broker_projection():
    rows = [
        {"id": "ok", "owner_user_id": "u", "pet_id": "p", "summary": "safe"},
        {"id": "other", "owner_user_id": "x", "pet_id": "p", "summary": "must not leak"},
    ]
    broker = ContextBroker({"PET_PROFILE": PetProfileContextSource(lambda _o, _p: rows)})
    bundle = broker.materialize("u", "p", ["PET_PROFILE"], capability_id="FECES_CURRENT_ASSESSMENT")
    assert [item["id"] for item in bundle["items"]] == ["ok"]


def test_current_media_source_is_explicitly_typed():
    source = CurrentMediaContextSource(lambda _o, _p: [])
    assert source.category == "CURRENT_MEDIA"
    assert source.load("u", "p") == []
