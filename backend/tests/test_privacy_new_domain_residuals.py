from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace

from app.agents.contracts import AgentOrchestrator
from app.billing.premium import PremiumEntitlement, PremiumService
from app.future.service import FutureItem
from app.operations.platform import OperationsService
from app.phase6 import Phase6Service
from app.phase6_firestore import FirestorePhase6Store
from app.portability.service import ShareGrant
from app.privacy.service import PrivacyService
from app.search.memory import PersonalPetMemory


def test_new_domain_residuals_are_counted_for_account_deletion():
    care = SimpleNamespace(records={"r": SimpleNamespace(owner_user_id="owner", deleted_at=None)})
    collaboration = SimpleNamespace(memberships={}, store=None)
    future = SimpleNamespace(items={})
    portability = SimpleNamespace(shares={})
    privacy = PrivacyService(
        pets=SimpleNamespace(list=lambda owner: []),
        media=SimpleNamespace(list_owned=lambda owner: []),
        phase6=SimpleNamespace(measurements={}, care={}),
        care_advanced=care, collaboration=collaboration, future=future, portability=portability,
    )
    result = privacy.deletion_verifier.verify("owner", {})
    assert result["verified"] is False
    assert result["residuals"] == {"advanced_care_records": 1}


def test_personal_memory_is_exported_as_a_canonical_domain():
    memory = SimpleNamespace(
        memories={"m": PersonalPetMemory("owner", "pet", "PREFERENCES", {"color": "blue"})},
        delete_owner=lambda owner: 1,
    )
    privacy = PrivacyService(
        pets=SimpleNamespace(list=lambda owner: []),
        media=SimpleNamespace(list_owned=lambda owner: []),
        phase6=SimpleNamespace(measurements={}, care={}),
        memory=memory,
    )
    exported = privacy.export("owner")
    assert len(exported["personal_pet_memories"]) == 1
    assert "personal_pet_memories" in exported["export_manifest"]["domains"]


def test_pet_export_is_scoped_to_requested_pet():
    @dataclass
    class Pet:
        id: str
        owner_user_id: str

    @dataclass
    class Measurement:
        owner_user_id: str
        animal_id: str
        deleted_at: object = None

    pets = [Pet("pet-1", "owner"), Pet("pet-2", "owner")]
    phase6 = SimpleNamespace(
        measurements={
            "m1": Measurement("owner", "pet-1"),
            "m2": Measurement("owner", "pet-2"),
        },
        care={},
    )
    privacy = PrivacyService(
        pets=SimpleNamespace(list=lambda owner: pets if owner == "owner" else []),
        media=SimpleNamespace(list_owned=lambda owner: []),
        phase6=phase6,
    )

    exported = privacy.export_pet("owner", "pet-1")

    assert [item["id"] for item in exported["pets"]] == ["pet-1"]
    assert [item["animal_id"] for item in exported["measurements"]] == ["pet-1"]
    assert "pet-2" not in str(exported)


def test_phase6_occurrences_and_preferences_are_exported_without_device_tokens():
    @dataclass
    class Pet:
        id: str
        owner_user_id: str

    pet = Pet("pet", "owner")
    phase6 = Phase6Service()
    pets = SimpleNamespace(list=lambda owner: [pet] if owner == "owner" else [], get=lambda owner, pet_id: pet)
    phase6.create_care(
        "owner", "pet", {"category": "CUSTOM", "title": "Brush", "due_at": datetime.now(UTC)}, "care-1", pets
    )
    phase6.preferences("owner")
    privacy = PrivacyService(
        pets=SimpleNamespace(list=lambda owner: [pet] if owner == "owner" else []),
        media=SimpleNamespace(list_owned=lambda owner: []), phase6=phase6,
    )
    exported = privacy.export("owner")
    assert len(exported["care_occurrences"]) == 1
    assert len(exported["notification_preferences"]) == 1
    assert "devices" not in exported


def test_agent_sessions_and_runs_are_exported_and_deleted_with_account():
    @dataclass
    class Pet:
        id: str
        owner_user_id: str

    pet = Pet("pet", "owner")
    agents = AgentOrchestrator()
    session = agents.create_session("owner", "pet")
    run = agents.create_run("owner", "summarize history", "pet", session_id=session.id)
    privacy = PrivacyService(
        pets=SimpleNamespace(
            list=lambda owner: [pet] if owner == "owner" else [],
            get=lambda *_: pet,
            delete=lambda *_: True,
        ),
        media=SimpleNamespace(list_owned=lambda owner: []),
        phase6=SimpleNamespace(measurements={}, care={}), agents=agents,
    )
    exported = privacy.export("owner")
    assert [item["id"] for item in exported["agent_runs"]] == [run.id]
    result = privacy.delete_account("owner", confirm=True, idempotency_key="agent-delete")
    assert result["status"] == "DELETED"
    assert run.id not in agents.runs
    assert session.id not in agents.sessions


def test_support_cases_are_removed_and_residual_checked_on_account_deletion():
    class Store:
        def __init__(self):
            self.rows = {}
            self.deleted = []

        def all(self, collection):
            return list(self.rows.values()) if collection == "support_cases" else []

        def put_raw(self, collection, key, data):
            self.rows[key] = data

        def delete(self, collection, key):
            self.deleted.append((collection, key))
            self.rows.pop(key, None)

    store = Store()
    operations = OperationsService(store=store)
    case = operations.report_problem("owner", {"category": "ACCOUNT", "message": "Please delete"})
    restarted = OperationsService(store=store)
    assert restarted.support[case.id].message == "Please delete"
    privacy = PrivacyService(
        pets=SimpleNamespace(list=lambda owner: [], delete=lambda *_: False),
        media=SimpleNamespace(list_owned=lambda owner: []),
        phase6=SimpleNamespace(measurements={}, care={}),
        operations=operations,
    )
    exported = privacy.export("owner")
    assert exported["support_cases"][0]["id"] == case.id
    residual = privacy.deletion_verifier.verify("owner", {})
    assert residual["residuals"] == {"support_cases": 1}
    result = privacy.delete_account("owner", confirm=True, idempotency_key="support-delete")
    assert result["status"] == "DELETED"
    assert case.id not in operations.support
    assert ("support_cases", case.id) in store.deleted


def test_firestore_store_includes_document_id_for_support_case_hydration():
    class Snapshot:
        id = "case-1"

        @staticmethod
        def to_dict():
            return {"owner_user_id": "owner", "category": "ACCOUNT", "message": "help", "support_code": "PETI-CASE"}

    class Collection:
        @staticmethod
        def stream():
            return [Snapshot()]

    class Client:
        @staticmethod
        def collection(_name):
            return Collection()

    rows = FirestorePhase6Store(Client()).all("support_cases")
    assert rows[0]["id"] == "case-1"


def test_privacy_export_never_contains_share_or_invitation_token_digests():
    future_item = FutureItem(
        "future-1", "owner", "pet", "INVITATION",
        payload={"token_digest": "future-secret-digest", "invitee": "caregiver@example.test"},
    )
    grant = ShareGrant("owner", "pet", "READ_ONLY", datetime.now(UTC), "share-1", "portable-secret-digest")
    privacy = PrivacyService(
        pets=SimpleNamespace(list=lambda owner: []),
        media=SimpleNamespace(list_owned=lambda owner: []),
        phase6=SimpleNamespace(measurements={}, care={}),
        future=SimpleNamespace(items={future_item.id: future_item}, public=lambda item: {
            "id": item.id, "owner_user_id": item.owner_user_id, "payload": {"invitee": "caregiver@example.test"}
        }),
        portability=SimpleNamespace(shares={grant.id: grant}),
    )
    exported = privacy.export("owner")
    assert "token_digest" not in exported["future_domain_items"][0]["payload"]
    assert "token_digest" not in exported["portability_share_grants"][0]


def test_privacy_export_uses_premium_public_redaction_for_purchase_tokens():
    premium = PremiumService(local_test_mode=True)
    entitlement = PremiumEntitlement(
        "entitlement-1", "owner", "peti_premium_monthly", "secret-purchase-token", "PURCHASED", "PREMIUM"
    )
    premium.entitlements[entitlement.id] = entitlement
    privacy = PrivacyService(
        pets=SimpleNamespace(list=lambda owner: []),
        media=SimpleNamespace(list_owned=lambda owner: []),
        phase6=SimpleNamespace(measurements={}, care={}), premium=premium,
    )
    exported = privacy.export("owner")
    assert "purchase_token" not in exported["premium_entitlements"][0]
