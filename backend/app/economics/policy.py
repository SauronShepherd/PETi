"""Deterministic cloud-economics controls; never changes safety semantics."""
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class CostProfile:
    profile_id: str
    operation_type: str
    estimated_units: int
    max_units: int
    version: str = "1.0.0"


class EconomicsPolicy:
    def __init__(self, profiles=None):
        self.profiles = profiles or {
            "PETI_CHECK": CostProfile("peti-check-v1", "PETI_CHECK", 1, 3),
            "SPECIALIST": CostProfile("specialist-v1", "SPECIALIST", 1, 3),
            "ASSISTANT": CostProfile("assistant-v1", "ASSISTANT", 1, 2),
            "REPORT_NARRATION": CostProfile("report-narration-v1", "REPORT_NARRATION", 1, 2),
        }
        self.kill_switch = False
        self.disabled_operations: set[str] = set()
        self.ledger: list[dict] = []

    def quote(self, operation_type: str, *, funded: bool = False) -> dict:
        profile = self.profiles.get(operation_type)
        if not profile:
            raise ValueError("COST_PROFILE_NOT_FOUND")
        return {"operation_type": operation_type, "profile_id": profile.profile_id, "profile_version": profile.version,
                "estimated_units": profile.estimated_units, "max_units": profile.max_units,
                "funded": funded, "available": not self.kill_switch and operation_type not in self.disabled_operations}

    def authorize(self, operation_type: str) -> None:
        if self.kill_switch or operation_type in self.disabled_operations:
            raise ValueError("AI_OPERATION_TEMPORARILY_DISABLED")
        self.quote(operation_type)

    def record(self, operation_id: str, operation_type: str, *, outcome: str, units: int = 0) -> dict:
        profile = self.profiles.get(operation_type)
        if not profile or units < 0 or units > profile.max_units:
            raise ValueError("COST_RECORD_INVALID")
        row = {"operation_id": operation_id, "operation_type": operation_type, "profile_id": profile.profile_id,
               "profile_version": profile.version, "units": units, "outcome": outcome,
               "recorded_at": datetime.now(UTC).isoformat()}
        self.ledger.append(row)
        return row
