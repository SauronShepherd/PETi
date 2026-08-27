from types import SimpleNamespace
from typing import ClassVar

from app.privacy.lifecycle import DeletionDependencyResolver
from app.privacy.service import PrivacyService


def test_deletion_plan_models_canonical_dependency_chain():
    plan = DeletionDependencyResolver().plan("u", "delete-1")
    assert plan.dependencies["records"] == ("candidate_facts", "documented_facts")
    assert plan.dependencies["documented_facts"] == ("measurements", "timeline")
    assert plan.dependencies["measurements"] == ("weekly_reports",)
    assert plan.dependencies["timeline"] == ("weekly_reports",)
    assert plan.dependencies["pets"] == ("account",)
    assert DeletionDependencyResolver().ordered_domains(plan) == tuple(plan.entities)
    assert "measurements" in plan.entities


def test_canonical_deletion_plan_executes_phase6_owner_purge():
    class Pets:
        def list(self, owner):
            return []

    class Media:
        def list_owned(self, owner):
            return []

    class Phase6:
        measurements: ClassVar[dict] = {}
        care: ClassVar[dict] = {}

        def __init__(self):
            self.called = False

        def remove_device_registrations(self, owner):
            return 0

        def remove_owner_data(self, owner):
            self.called = True
            return {}

    phase6 = Phase6()
    service = PrivacyService(Pets(), Media(), phase6)
    result = service.delete_account("u", confirm=True, idempotency_key="phase6-delete")
    assert result["status"] == "DELETED"
    assert phase6.called is True


def test_active_premium_state_does_not_block_account_deletion():
    class Pets:
        def __init__(self):
            self.items = [SimpleNamespace(id="pet-1", owner_user_id="u", deleted_at=None)]
        def list(self, owner):
            return [item for item in self.items if item.owner_user_id == owner and item.deleted_at is None]
        def delete(self, owner, pet_id):
            for item in self.items:
                if item.owner_user_id == owner and item.id == pet_id:
                    item.deleted_at = True
                    return True
            return False

    class Media:
        def list_owned(self, owner):
            return []

    class Phase6:
        measurements: ClassVar[dict] = {}
        care: ClassVar[dict] = {}
        def remove_device_registrations(self, owner):
            return 0

    premium = SimpleNamespace(entitlements={"u": SimpleNamespace(owner_user_id="u", state="ACTIVE")})
    service = PrivacyService(Pets(), Media(), Phase6(), premium=premium)
    result = service.delete_account("u", confirm=True, idempotency_key="premium-delete")
    assert result["status"] == "DELETED"
    assert result["job"]["state"] == "COMPLETE"
    assert result["job"]["completed"] == [
        "FREEZE_ACCOUNT", "CANCEL_QUEUED_WORK", "DELETE_DERIVED_DATA",
        "DELETE_CANONICAL_DATA", "DELETE_OBJECTS", "VERIFY_NO_RESIDUAL_DATA",
    ]


def test_account_deletion_cleans_owner_rows_without_a_live_pet():
    class Pets:
        def list(self, owner):
            return []

        def delete(self, owner, pet_id):
            return False

    class Media:
        def list_owned(self, owner):
            return []

    class Phase6:
        measurements: ClassVar[dict] = {}
        care: ClassVar[dict] = {}

        def remove_device_registrations(self, owner):
            return 0

    class Records:
        def __init__(self):
            self.documents = {"d1": SimpleNamespace(owner_user_id="u", id="d1", deleted_at=None)}
            self.candidates = {}
            self.facts = {}

        def delete(self, owner, document_id, confirm_dependencies=False):
            self.documents[document_id].deleted_at = True
            return True

    records = Records()
    service = PrivacyService(Pets(), Media(), Phase6(), records=records)
    result = service.delete_account("u", confirm=True, idempotency_key="orphan-delete")
    assert result["status"] == "DELETED"
    assert records.documents["d1"].deleted_at is True
