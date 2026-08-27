from datetime import UTC, datetime

from app.domain.users import UserRole
from app.repositories.firestore import FirestoreAnimalRepository, FirestoreUserRepository


class Doc:
    def __init__(self, data):
        self.data = data
        self.exists = True

    def to_dict(self):
        return self.data


class Ref:
    def __init__(self, data=None):
        self.data = data

    def get(self):
        return Doc(self.data) if self.data else type("Missing", (), {"exists": False})()

    def create(self, data):
        self.data = data


class Collection:
    def __init__(self, data):
        self.data = data

    def document(self, _):
        return Ref(self.data)

    def where(self, *_):
        return self

    def stream(self):
        return [Doc(self.data)]


class Client:
    def __init__(self, data):
        self.data = data

    def collection(self, _):
        return Collection(self.data)


class UserRef:
    def __init__(self, data):
        self.data = data

    def get(self):
        if not self.data:
            return type("Missing", (), {"exists": False})()
        return Doc(self.data)

    def create(self, data):
        self.data.update(data)

    def update(self, updates):
        self.data.update(updates)


class UserCollection:
    def __init__(self, data):
        self.data = data

    def document(self, _):
        return UserRef(self.data)


class UserClient:
    def __init__(self):
        self.data = {}

    def collection(self, _):
        return UserCollection(self.data)


def test_firestore_animal_adapter_enforces_owner_on_reads():
    now = datetime.now(UTC)
    data = {
        "id": "p",
        "owner_user_id": "a",
        "species": "DOG",
        "display_name": "Milo",
        "active_state": "ACTIVE",
        "avatar_media_id": None,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }
    repo = FirestoreAnimalRepository(Client(data))
    assert repo.get_owned("a", "p").id == "p"
    assert repo.get_owned("b", "p") is None


def test_firestore_user_provision_persists_role_persona_and_exemptions():
    client = UserClient()
    repo = FirestoreUserRepository(client)

    user = repo.provision("firebase-1", UserRole.INTERNAL_TEST, "qa-persona")

    assert user.role == UserRole.INTERNAL_TEST
    assert user.internal_persona_code == "qa-persona"
    assert user.billing_exempt is True
    assert user.ads_exempt is True
    assert client.data["role"] == "INTERNAL_TEST"
    assert client.data["internal_persona_code"] == "qa-persona"
