import pytest
from app.operations.controls import RETENTION_CATEGORIES, AbuseGuard
from app.operations.platform import FirestoreFeatureFlagStore, OperationsService


def test_abuse_guard_has_stable_limit_and_retention_categories():
    guard = AbuseGuard(max_requests=1)
    assert guard.check_and_record("u").allowed
    limited = guard.check_and_record("u")
    assert not limited.allowed and limited.code == "FUNDING_RATE_LIMITED"
    assert {x.name for x in RETENTION_CATEGORIES} >= {"OPERATIONAL_LEDGER", "SECURITY_FRAUD"}


class FlagStore:
    def __init__(self, flags=None):
        self.flags = dict(flags or {})
        self.saved = []

    def load(self):
        return dict(self.flags)

    def save(self, flags):
        self.flags = dict(flags)
        self.saved.append(dict(flags))


def test_feature_flags_hydrate_and_persist_across_service_instances():
    store = FlagStore()
    first = OperationsService(flag_store=store)
    assert first.set_ai_global_kill_switch(True, "ADMIN") is True
    assert store.saved
    second = OperationsService(flag_store=store)
    assert second.flags["ai_global_kill_switch"] is True
    second.set_scoped_flags("provider", {"GEMINI": True}, "ADMIN")
    assert store.flags["ai_provider_kill_switches"] == {"GEMINI": True}


def test_specialist_defaults_are_disabled_until_certified():
    flags = OperationsService().flags
    assert flags["premium_enabled"] is False
    for capability in ("dog_initial_scan", "dog_dental_check", "dog_feces_check", "dog_body_check"):
        assert flags[f"{capability}_enabled"] is False
        assert flags[f"{capability}_public_enabled"] is False


def test_malformed_durable_boolean_flags_keep_safe_defaults():
    store = FlagStore({
        "dog_body_check_enabled": "true",
        "dog_body_check_public_enabled": 1,
        "weekly_reports_enabled": "false",
    })
    flags = OperationsService(flag_store=store).flags
    assert flags["dog_body_check_enabled"] is False
    assert flags["dog_body_check_public_enabled"] is False
    assert flags["weekly_reports_enabled"] is True


def test_variable_cost_switch_persists_across_restart():
    store = FlagStore()
    first = OperationsService(flag_store=store)
    assert first.set_variable_cost_intake(False, "ADMIN") is False
    second = OperationsService(flag_store=store)
    assert second.variable_cost_intake_allowed() is False


def test_budget_exhaustion_persists_emergency_variable_cost_shutdown():
    store = FlagStore()
    service = OperationsService(flag_store=store)
    service.costs.policy = service.costs.policy.__class__("TEST", "DAILY", 1)
    decision = service.request_variable_cost_operation("AI_SPECIALIST_STANDARD", 2)
    assert decision.allowed is False
    assert OperationsService(flag_store=store).variable_cost_intake_allowed() is False


def test_scoped_kill_switch_service_contract_rejects_invalid_scope_and_values():
    service = OperationsService()
    with pytest.raises(PermissionError, match="ADMIN_REQUIRED"):
        service.set_scoped_flags("provider", {}, "CUSTOMER")
    with pytest.raises(ValueError, match="SCOPE_INVALID"):
        service.set_scoped_flags("unknown", {}, "ADMIN")
    with pytest.raises(ValueError, match="VALUES_INVALID"):
        service.set_scoped_flags("provider", {"GEMINI": "true"}, "ADMIN")


def test_global_and_variable_controls_reject_non_boolean_values():
    service = OperationsService()
    with pytest.raises(TypeError, match="AI_GLOBAL_KILL_SWITCH_INVALID"):
        service.set_ai_global_kill_switch("true", "ADMIN")
    with pytest.raises(TypeError, match="VARIABLE_COST_FLAG_INVALID"):
        service.set_variable_cost_intake(1, "ADMIN")


def test_variable_cost_requests_reject_negative_or_non_integer_estimates():
    service = OperationsService()
    with pytest.raises(ValueError, match="AI_COST_UNITS_INVALID"):
        service.request_variable_cost_operation("AI", -1)
    with pytest.raises(ValueError, match="AI_COST_UNITS_INVALID"):
        service.request_variable_cost_operation("AI", "1")


def test_persisted_kill_switches_are_reapplied_to_analysis_after_restart():
    store = FlagStore({
        "ai_global_kill_switch": True,
        "ai_provider_kill_switches": {"GEMINI": True, "bad": "true"},
        "ai_model_kill_switches": {"gemini-2.5": True},
    })
    analysis = type("Analysis", (), {
        "ai_enabled": True,
        "provider_kill_switches": {},
        "model_kill_switches": {},
        "species_kill_switches": {},
    })()
    OperationsService(flag_store=store).apply_to_analysis(analysis)
    assert analysis.ai_enabled is False
    assert analysis.provider_kill_switches == {"GEMINI": True}
    assert analysis.model_kill_switches == {"gemini-2.5": True}


class Snapshot:
    def __init__(self, data):
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return self._data


class Document:
    def __init__(self, bucket):
        self.bucket = bucket

    def get(self):
        return Snapshot(self.bucket.get("runtime"))

    def set(self, data):
        self.bucket["runtime"] = data


class Collection:
    def __init__(self, bucket):
        self.bucket = bucket

    def document(self, document_id):
        assert document_id == "runtime"
        return Document(self.bucket)


class FirestoreClient:
    def __init__(self):
        self.data = {}

    def collection(self, name):
        assert name == "peti_feature_flags"
        return Collection(self.data)


def test_firestore_feature_flag_store_round_trip():
    store = FirestoreFeatureFlagStore(FirestoreClient())
    store.save({"ai_global_kill_switch": True})
    assert store.load() == {"ai_global_kill_switch": True}
