import hashlib

from app.future.service import FutureService


class Pets:
    def get(self, owner, pet_id):
        return {"owner": owner, "id": pet_id}


def test_future_share_does_not_persist_raw_token():
    class Store:
        def __init__(self):
            self.rows = {}

        def put_raw(self, collection, key, data):
            self.rows[key] = data

        def all(self, collection):
            return list(self.rows.values())

    store = Store()
    service = FutureService(Pets(), store=store)
    export = service.export("owner-1", "pet-1")
    share = service.share("owner-1", export.id, {"scope": "READ_ONLY"})
    persisted = store.rows[share["id"]]

    assert "token_digest" not in share["payload"]
    assert persisted["payload"]["token_digest"] == hashlib.sha256(share["token"].encode()).hexdigest()
    assert "token" not in persisted["payload"]
    assert "token_digest" not in service.public(service.items[share["id"]])["payload"]
