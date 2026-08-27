import asyncio
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from app.auth.verifiers import FirebaseIdentityVerifier, LocalTestIdentityVerifier


def test_local_auth_accepts_only_explicit_local_shape():
    identity = asyncio.run(
        LocalTestIdentityVerifier().verify_bearer_token("local-test:test-user-a")
    )
    assert identity.firebase_uid == "test-user-a"
    for token in ("", "Bearer abc", "local-test:", "local-test:bad space"):
        try:
            asyncio.run(LocalTestIdentityVerifier().verify_bearer_token(token))
            assert False
        except ValueError:
            pass


def test_local_auth_rejects_non_string_token():
    try:
        asyncio.run(LocalTestIdentityVerifier().verify_bearer_token(None))
        assert False
    except ValueError:
        pass


def test_local_auth_rejects_oversized_identity():
    with pytest.raises(ValueError):
        asyncio.run(LocalTestIdentityVerifier().verify_bearer_token("local-test:" + "a" * 129))


def test_firebase_identity_verifier_accepts_uid_or_subject():
    class FirebaseAuth:
        def __init__(self, decoded):
            self.decoded = decoded

        def verify_id_token(self, _token):
            return self.decoded

    assert asyncio.run(
        FirebaseIdentityVerifier(FirebaseAuth({"uid": "firebase-user"})).verify_bearer_token("token")
    ).firebase_uid == "firebase-user"
    assert asyncio.run(
        FirebaseIdentityVerifier(FirebaseAuth({"sub": "subject-user"})).verify_bearer_token("token")
    ).firebase_uid == "subject-user"


def test_firebase_identity_verifier_normalizes_bad_claims_and_provider_errors():
    class FirebaseAuth:
        def __init__(self, decoded=None, error=None):
            self.decoded, self.error = decoded, error

        def verify_id_token(self, _token):
            if self.error:
                raise self.error
            return self.decoded

    for auth in (
        FirebaseAuth({"uid": ""}),
        FirebaseAuth({"uid": "   "}),
        FirebaseAuth({"uid": 123}),
        FirebaseAuth({"uid": "a" * 129}),
        FirebaseAuth(error=RuntimeError("invalid")),
    ):
        try:
            asyncio.run(FirebaseIdentityVerifier(auth).verify_bearer_token("token"))
            assert False
        except ValueError:
            pass


def test_firebase_identity_verifier_rejects_empty_token_before_provider_call():
    class FirebaseAuth:
        def __init__(self):
            self.called = False

        def verify_id_token(self, _token):
            self.called = True
            return {"uid": "unexpected"}

    firebase_auth = FirebaseAuth()
    for token in ("", "   ", None):
        try:
            asyncio.run(FirebaseIdentityVerifier(firebase_auth).verify_bearer_token(token))
            assert False
        except ValueError:
            pass
    assert firebase_auth.called is False


def test_roles_are_not_client_supplied():
    from app.main import app
    from fastapi.testclient import TestClient

    response = TestClient(app).get(
        "/v1/me", headers={"Authorization": "Bearer local-test:role-test", "X-Role": "ADMIN"}
    )
    assert response.status_code == 200 and response.json()["role"] == "CUSTOMER"


def test_request_auth_normalizes_unexpected_identity_verifier_failure():
    from app.main import app
    from fastapi.testclient import TestClient

    class BrokenVerifier:
        async def verify_bearer_token(self, _token):
            raise RuntimeError("verifier unavailable")

    original = app.state.identity_verifier
    app.state.identity_verifier = BrokenVerifier()
    try:
        response = TestClient(app).get(
            "/v1/me", headers={"Authorization": "Bearer valid-shaped-token"}
        )
    finally:
        app.state.identity_verifier = original
    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_INVALID_TOKEN"


def test_request_auth_does_not_mask_user_store_failure_as_auth_failure():
    from app.main import app
    from fastapi.testclient import TestClient

    class BrokenUsers:
        def get_or_create(self, _firebase_uid):
            raise RuntimeError("user store unavailable")

    original = app.state.users
    app.state.users = BrokenUsers()
    try:
        response = TestClient(app, raise_server_exceptions=False).get(
            "/v1/me", headers={"Authorization": "Bearer local-test:store-failure"}
        )
    finally:
        app.state.users = original
    assert response.status_code == 500
    assert response.text == "Internal Server Error"


def test_concurrent_first_login_provisions_one_user():
    from app.repositories.memory import InMemoryUserRepository

    repository = InMemoryUserRepository()
    with ThreadPoolExecutor(max_workers=16) as pool:
        users = list(pool.map(lambda _: repository.get_or_create("same-firebase-uid"), range(16)))
    assert len({user.id for user in users}) == 1
    assert len(repository.by_uid) == 1


def test_firestore_user_repository_creates_and_reads_without_transaction_client():
    from app.repositories.firestore import FirestoreUserRepository

    class Snapshot:
        def __init__(self, data=None): self._data = data
        @property
        def exists(self): return self._data is not None
        def to_dict(self): return dict(self._data)

    class Document:
        def __init__(self, data): self.data = data
        def get(self): return Snapshot(self.data)
        def create(self, data): self.data = dict(data)

    class Collection:
        def __init__(self): self.docs = {}
        def document(self, key):
            self.docs.setdefault(key, Document(None))
            return self.docs[key]

    class Client:
        def __init__(self): self.users = Collection()
        def collection(self, name): assert name == "users"; return self.users

    repository = FirestoreUserRepository(Client())
    created = repository.get_or_create("firebase-1")
    loaded = repository.get_or_create("firebase-1")
    assert created.id == loaded.id == "firebase-1"
    assert created.role == loaded.role


def test_firestore_user_repository_rereads_winner_after_already_exists():
    from app.repositories.firestore import FirestoreUserRepository

    class AlreadyExists(RuntimeError):
        pass

    class Snapshot:
        exists = True
        def to_dict(self): return {"id": "uid", "firebase_uid": "uid", "role": "CUSTOMER", "billing_exempt": False, "ads_exempt": False, "internal_persona_code": None, "created_at": None, "updated_at": None, "deleted_at": None}

    class Document:
        def get(self): return Snapshot()
        def create(self, _data):
            raise AlreadyExists("winner created concurrently")

    class Client:
        def collection(self, _name): return self
        def document(self, _key): return Document()

    user = FirestoreUserRepository(Client()).get_or_create("uid")
    assert user.id == "uid"


def test_real_admin_role_does_not_bypass_pet_ownership():
    from app.domain.users import UserRole
    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    owner = "owner-" + uuid4().hex
    admin = "admin-" + uuid4().hex
    internal = "internal-test-" + uuid4().hex
    owner_headers = {"Authorization": f"Bearer local-test:{owner}"}
    admin_headers = {"Authorization": f"Bearer local-test:{admin}"}
    internal_headers = {"Authorization": f"Bearer local-test:{internal}"}
    created = client.post(
        "/v1/pets", headers={**owner_headers, "Idempotency-Key": "pet-" + owner},
        json={"species": "DOG", "display_name": "Owned pet"},
    )
    assert created.status_code == 201
    app.state.users.provision(admin, UserRole.ADMIN)
    app.state.users.provision(internal, UserRole.INTERNAL_TEST)
    pet_id = created.json()["id"]
    assert client.get(f"/v1/pets/{pet_id}", headers=admin_headers).status_code == 404
    assert client.get("/v1/pets", headers=admin_headers).json() == []
    assert client.get(f"/v1/pets/{pet_id}", headers=internal_headers).status_code == 404
    assert client.get("/v1/pets", headers=internal_headers).json() == []


def test_memory_route_rejects_missing_or_non_owned_pet():
    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    headers = {"Authorization": f"Bearer local-test:memory-owner-{uuid4().hex}"}

    response = client.get(f"/v1/pets/missing-{uuid4().hex}/memory", headers=headers)

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_customer_crud_operations_are_cross_user_isolated():
    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    owner = "crud-owner-" + uuid4().hex
    other = "crud-other-" + uuid4().hex
    owner_headers = {"Authorization": f"Bearer local-test:{owner}"}
    other_headers = {"Authorization": f"Bearer local-test:{other}"}
    created = client.post(
        "/v1/pets",
        headers={**owner_headers, "Idempotency-Key": "crud-" + owner},
        json={"species": "DOG", "display_name": "Owner pet"},
    )
    assert created.status_code == 201
    pet_id = created.json()["id"]

    assert client.get(f"/v1/pets/{pet_id}", headers=other_headers).status_code == 404
    assert client.get("/v1/pets", headers=other_headers).json() == []
    assert client.patch(
        f"/v1/pets/{pet_id}", headers=other_headers, json={"display_name": "Hijacked"}
    ).status_code == 404
    assert client.delete(f"/v1/pets/{pet_id}", headers=other_headers).status_code == 404
    assert client.get(f"/v1/pets/{pet_id}", headers=owner_headers).json()["display_name"] == "Owner pet"


def test_care_records_are_cross_user_isolated():
    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    owner = "care-owner-" + uuid4().hex
    other = "care-other-" + uuid4().hex
    owner_headers = {"Authorization": f"Bearer local-test:{owner}"}
    other_headers = {"Authorization": f"Bearer local-test:{other}"}
    pet = client.post(
        "/v1/pets", headers={**owner_headers, "Idempotency-Key": "care-pet-" + owner},
        json={"species": "DOG", "display_name": "Care pet"},
    ).json()
    pet_id = pet["id"]
    created = client.post(
        f"/v1/pets/{pet_id}/care-records", headers=owner_headers,
        json={"record_type": "VACCINATION", "payload": {"name": "Rabies"}},
    )
    assert created.status_code == 201
    assert len(client.get(f"/v1/pets/{pet_id}/care-records", headers=owner_headers).json()) == 1
    assert client.get(f"/v1/pets/{pet_id}/care-records", headers=other_headers).json() == []
    assert client.post(
        f"/v1/pets/{pet_id}/care-records", headers=other_headers,
        json={"record_type": "VACCINATION", "payload": {"name": "Hijack"}},
    ).status_code == 404


def test_account_deletion_is_bound_to_authenticated_owner():
    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    owner = "delete-owner-" + uuid4().hex
    other = "delete-other-" + uuid4().hex
    owner_headers = {"Authorization": f"Bearer local-test:{owner}"}
    other_headers = {"Authorization": f"Bearer local-test:{other}"}
    pet = client.post(
        "/v1/pets", headers={**owner_headers, "Idempotency-Key": "delete-pet-" + owner},
        json={"species": "DOG", "display_name": "Delete isolation pet"},
    ).json()
    other_delete = client.delete(
        "/v1/me/account", headers={**other_headers, "Idempotency-Key": "delete-other-key"},
        params={"confirm": "true"},
    )
    assert other_delete.status_code == 200
    assert client.get(f"/v1/pets/{pet['id']}", headers=owner_headers).status_code == 200
    assert client.get("/v1/me/account-deletion/delete-other-key", headers=owner_headers).status_code == 404
