import pytest
from app.agent_runtime.context_broker import ContextBroker


def test_policy_rejects_dental_for_feces_specialist():
    with pytest.raises(ValueError, match="CONTEXT_CATEGORY_FORBIDDEN"):
        ContextBroker({"DENTAL_HISTORY": lambda *_: []}).materialize("u1", "p1", ["DENTAL_HISTORY"], capability_id="FECES_CURRENT_ASSESSMENT")

def test_media_projection_is_scoped_and_has_no_url_and_is_immutable():
    broker = ContextBroker({"CURRENT_MEDIA": lambda *_: [{"owner_user_id": "u1", "pet_id": "p1", "id": "m1", "url": "secret", "checksum": "abc"}]})
    bundle = broker.materialize("u1", "p1", ["CURRENT_MEDIA"], capability_id="FECES_CURRENT_ASSESSMENT")
    assert "url" not in bundle["items"][0]; bundle["items"].clear(); assert broker.get(bundle["id"])["items"]
