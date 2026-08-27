import pytest
from app.domain.users import UserRole

from scripts import provision_user_role
from scripts.provision_user_role import validate_inputs


def test_provision_validation_accepts_internal_persona_for_internal_role():
    validate_inputs("firebase-user", UserRole.INTERNAL_TEST, "qa-persona")


@pytest.mark.parametrize(
    ("firebase_uid", "role", "persona"),
    [
        ("", UserRole.ADMIN, None),
        ("firebase-user", UserRole.CUSTOMER, "qa-persona"),
        ("firebase-user", UserRole.ADMIN, "   "),
    ],
)
def test_provision_validation_rejects_unsafe_inputs(firebase_uid, role, persona):
    with pytest.raises(ValueError):
        validate_inputs(firebase_uid, role, persona)


def test_build_repository_targets_firestore_by_default(monkeypatch):
    created = {}

    class FakeClient:
        def __init__(self, project=None):
            created["project"] = project

    class FakeFirestore:
        Client = FakeClient

    class FakeRepository:
        def __init__(self, client):
            created["client"] = client

    monkeypatch.setitem(__import__("sys").modules, "google.cloud.firestore", FakeFirestore)
    monkeypatch.setattr("app.repositories.firestore.FirestoreUserRepository", FakeRepository)

    repository = provision_user_role.build_repository(False, "qualification-project")

    assert isinstance(repository, FakeRepository)
    assert created["project"] == "qualification-project"
    assert isinstance(created["client"], FakeClient)
