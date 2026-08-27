"""Phase 15–20 operational controls, support diagnostics, and feature flags."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any, Protocol
from uuid import uuid4

from .reconciliation import ReconciliationService


@dataclass
class SupportCase:
    id: str
    owner_user_id: str
    category: str
    message: str
    support_code: str
    status: str = "OPEN"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class ProviderPricingPolicy:
    id: str = "provider-pricing-v1"
    units_per_dollar: int = 1_000_000
    provider: str = "GEMINI"


@dataclass(frozen=True)
class BudgetDecision:
    allowed: bool
    level: str
    consumed_units: int
    max_units: int
    reason: str


class FeatureFlagStore(Protocol):
    def load(self) -> dict[str, object]: ...
    def save(self, flags: dict[str, object]) -> None: ...


class FirestoreFeatureFlagStore:
    """Small server-authoritative flag document adapter."""
    def __init__(self, client: Any, document_id: str = "runtime"):
        self.client = client
        self.document_id = document_id

    def load(self) -> dict[str, object]:
        snapshot = self.client.collection("peti_feature_flags").document(self.document_id).get()
        return dict(snapshot.to_dict() or {}) if snapshot.exists else {}

    def save(self, flags: dict[str, object]) -> None:
        self.client.collection("peti_feature_flags").document(self.document_id).set(dict(flags))


class CostAttributionService:
    """Payload-free cost ledger and deterministic budget gate."""
    def __init__(self, policy: SpendBudgetPolicy | None = None, pricing: ProviderPricingPolicy | None = None):
        self.policy = policy or SpendBudgetPolicy("DEV", "DAILY", 25_000_000)
        self.pricing = pricing or ProviderPricingPolicy()
        self.records: dict[str, AICostRecord] = {}
        self.lock = RLock()

    def record(self, analysis_id: str, operation_type: str, estimated_units: int, actual_units: int | None = None, provider: str | None = None) -> AICostRecord:
        if estimated_units < 0 or actual_units is not None and actual_units < 0:
            raise ValueError("AI_COST_UNITS_INVALID")
        with self.lock:
            item = AICostRecord(uuid4().hex, analysis_id, operation_type, estimated_units, actual_units, provider or self.pricing.provider)
            self.records[item.id] = item
            return item

    def consumed_units(self) -> int:
        return sum(item.actual_units if item.actual_units is not None else item.estimated_units for item in self.records.values())

    def decide(self, additional_units: int = 0) -> BudgetDecision:
        consumed = self.consumed_units()
        projected = consumed + max(0, additional_units)
        limit = self.policy.max_units
        if not self.policy.enabled:
            return BudgetDecision(True, "DISABLED", consumed, limit, "BUDGET_POLICY_DISABLED")
        if projected > limit:
            return BudgetDecision(False, "EMERGENCY", consumed, limit, "AI_COST_BUDGET_EXCEEDED")
        level = "CRITICAL" if projected >= limit * 0.9 else "WARNING" if projected >= limit * 0.8 else "OK"
        return BudgetDecision(True, level, consumed, limit, "OK")


class OperationsService:
    def __init__(self, analytics=None, flag_store: FeatureFlagStore | None = None, store=None):
        self.analytics = analytics
        self.flag_store = flag_store
        self.store = store
        self.flags: dict[str, object] = {
            "dog_initial_scan_enabled": False,
            "dog_initial_scan_evaluation_certificate_id": "PENDING",
            "dog_initial_scan_public_enabled": False,
            "dog_initial_scan_coat_color_enabled": True,
            "dog_initial_scan_coat_pattern_enabled": True,
            "dog_initial_scan_coat_length_enabled": True,
            "dog_initial_scan_morphology_enabled": True,
            "dog_initial_scan_distinguishing_features_enabled": True,
            "dog_dental_check_enabled": False,
            "dog_dental_check_evaluation_certificate_id": "PENDING",
            "dog_dental_check_public_enabled": False,
            "dog_dental_check_area_of_concern_enabled": True,
            "dog_dental_check_source_regions_enabled": True,
            "dog_dental_check_calculus_like_enabled": True,
            "dog_dental_check_gingival_redness_enabled": True,
            "dog_dental_check_swelling_enabled": True,
            "dog_dental_check_bleeding_enabled": True,
            "dog_dental_check_recession_like_enabled": True,
            "dog_dental_check_tooth_damage_enabled": True,
            "dog_dental_check_discoloration_enabled": True,
            "dog_dental_check_missing_tooth_like_enabled": True,
            "dog_dental_check_lesion_like_enabled": True,
            "dog_dental_check_foreign_material_like_enabled": True,
            "dog_feces_check_enabled": False,
            "dog_feces_check_evaluation_certificate_id": "PENDING",
            "dog_feces_check_public_enabled": False,
            "dog_feces_check_source_regions_enabled": True,
            "dog_feces_check_color_observation_enabled": True,
            "dog_feces_check_consistency_enabled": True,
            "dog_feces_check_mucus_like_enabled": True,
            "dog_feces_check_fresh_red_blood_like_enabled": True,
            "dog_feces_check_dark_black_tarry_like_enabled": True,
            "dog_feces_check_foreign_material_like_enabled": True,
            "dog_feces_check_worm_segment_like_enabled": True,
            "dog_feces_longitudinal_compare_enabled": False,
            "dog_body_check_enabled": False,
            "dog_body_check_evaluation_certificate_id": "PENDING",
            "dog_body_check_public_enabled": False,
            "dog_body_condition_category_enabled": True,
            "dog_body_longitudinal_compare_enabled": True,
            "dog_body_ai_weight_estimate_enabled": False,
            "dog_body_source_regions_enabled": True,
            "weekly_reports_enabled": True,
            # Monetization is out of scope for the current free submission.
            # Keep the dormant billing boundary fail-closed until a separately
            # reviewed release explicitly enables it.
            "premium_enabled": False,
            "emergency_variable_cost_operations_disabled": False,
            "ai_global_kill_switch": False,
        }
        if self.flag_store:
            # A malformed durable flag must never become truthy through Python's
            # string coercion rules. Unknown/non-boolean feature switches are
            # ignored and retain their fail-closed defaults.
            for key, value in self.flag_store.load().items():
                if key.endswith("_enabled") or key in {"ai_global_kill_switch", "emergency_variable_cost_operations_disabled"}:
                    if isinstance(value, bool):
                        self.flags[key] = value
                    continue
                self.flags[key] = value
        self.support: dict[str, SupportCase] = {}
        if self.store and hasattr(self.store, "all"):
            try:
                rows = self.store.all("support_cases")
            except Exception:  # noqa: BLE001 - unavailable support data must not block startup
                rows = []
            for row in rows:
                try:
                    case = SupportCase(**row)
                    self.support[case.id] = case
                except (TypeError, KeyError, ValueError):
                    continue
        self.costs = CostAttributionService()
        self.reconciliation = ReconciliationService()
        self.lock = RLock()

    def support_code(self, owner, category="GENERAL"):
        case = SupportCase(uuid4().hex, owner, category, "", "PETI-" + uuid4().hex[:10].upper())
        self.support[case.id] = case
        if self.store and hasattr(self.store, "put_raw"):
            self.store.put_raw("support_cases", case.id, asdict(case))
        return case

    def report_problem(self, owner, body):
        case = self.support_code(owner, body.get("category", "GENERAL")); case.message = str(body.get("message", ""))[:2_000]
        if self.store and hasattr(self.store, "put_raw"):
            self.store.put_raw("support_cases", case.id, asdict(case))
        return case

    def metrics(self):
        events = self.analytics.events if self.analytics else []
        return {
            "analytics_event_count": len(events),
            "events_by_type": {event: sum(1 for x in events if x.get("event") == event) for event in sorted({x.get("event") for x in events})},
            "feature_flags": dict(self.flags),
            "support_open": sum(1 for x in self.support.values() if x.status == "OPEN"),
            "ai_cost_records": len(self.costs.records),
            "ai_cost_units": self.costs.consumed_units(),
            "ai_budget": self.costs.decide(),
            "reconciliation": [asdict(item) for item in self.reconciliation.snapshot()],
        }

    def reconcile(self, domain, operation_key, action):
        return self.reconciliation.reconcile(domain, operation_key, action)

    def set_variable_cost_intake(self, enabled: bool, actor_role: str) -> bool:
        if actor_role != "ADMIN":
            raise PermissionError("OPERATIONS_ADMIN_REQUIRED")
        if not isinstance(enabled, bool):
            raise TypeError("VARIABLE_COST_FLAG_INVALID")
        self.flags["emergency_variable_cost_operations_disabled"] = not enabled
        self._persist_flags()
        return enabled

    def variable_cost_intake_allowed(self) -> bool:
        return not bool(self.flags["emergency_variable_cost_operations_disabled"])

    def set_ai_global_kill_switch(self, enabled: bool, actor_role: str) -> bool:
        if actor_role != "ADMIN":
            raise PermissionError("OPERATIONS_ADMIN_REQUIRED")
        if not isinstance(enabled, bool):
            raise TypeError("AI_GLOBAL_KILL_SWITCH_INVALID")
        self.flags["ai_global_kill_switch"] = bool(enabled)
        self._persist_flags()
        return bool(enabled)

    def set_scoped_flags(self, scope: str, values: dict[str, bool], actor_role: str = "") -> None:
        if actor_role != "ADMIN":
            raise PermissionError("OPERATIONS_ADMIN_REQUIRED")
        if scope not in {"provider", "model", "species"}:
            raise ValueError("AI_KILL_SWITCH_SCOPE_INVALID")
        if not isinstance(values, dict) or any(not isinstance(key, str) or not isinstance(value, bool) for key, value in values.items()):
            raise ValueError("AI_KILL_SWITCH_VALUES_INVALID")
        self.flags[f"ai_{scope}_kill_switches"] = dict(values)
        self._persist_flags()

    def _persist_flags(self) -> None:
        if self.flag_store:
            self.flag_store.save(self.flags)

    def apply_to_analysis(self, analysis) -> None:
        """Reapply durable kill switches after an analysis service restart."""
        if self.flags.get("ai_global_kill_switch") is True:
            analysis.ai_enabled = False
        for scope in ("provider", "model", "species"):
            values = self.flags.get(f"ai_{scope}_kill_switches", {})
            if isinstance(values, dict):
                setattr(
                    analysis,
                    f"{scope}_kill_switches",
                    {key: value for key, value in values.items() if isinstance(key, str) and isinstance(value, bool)},
                )

    def request_variable_cost_operation(self, operation_type: str, estimated_units: int) -> BudgetDecision:
        if not isinstance(estimated_units, int) or isinstance(estimated_units, bool) or estimated_units < 0:
            raise ValueError("AI_COST_UNITS_INVALID")
        if not self.variable_cost_intake_allowed():
            return BudgetDecision(False, "EMERGENCY", self.costs.consumed_units(), self.costs.policy.max_units, "VARIABLE_COST_INTAKE_DISABLED")
        decision = self.costs.decide(estimated_units)
        if not decision.allowed:
            self.flags["emergency_variable_cost_operations_disabled"] = True
            self._persist_flags()
        return decision

    @staticmethod
    def public(value): return asdict(value)
@dataclass
class StructuredLogEnvelope:
    timestamp: str
    severity: str
    environment: str
    event_name: str
    correlation_id: str
    labels: dict = field(default_factory=dict)


@dataclass
class AICostRecord:
    id: str
    analysis_id: str
    operation_type: str
    estimated_units: int
    actual_units: int | None = None
    provider: str | None = None


@dataclass(frozen=True)
class SpendBudgetPolicy:
    environment: str
    period: str
    max_units: int
    enabled: bool = True


@dataclass(frozen=True)
class ModelConfig:
    id: str
    provider: str
    model: str
    prompt_version: str
    schema_version: str
    enabled: bool = False


class IncidentSeverity:
    SEV0 = "SEV0"; SEV1 = "SEV1"; SEV2 = "SEV2"; SEV3 = "SEV3"
