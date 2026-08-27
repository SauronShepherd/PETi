"""Generic Phase 20C specialist capability framework.

Candidate domains are data-driven and remain disabled until a release certificate
binds capture, schema, guardrails, evaluation and operations policy.
"""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SpecialistCapability:
    capability_id: str
    species: str
    analysis_type: str
    evidence_types: tuple[str, ...]
    schema_version: str
    safety_policy_version: str
    status: str = "INTERNAL"
    certificate_id: str | None = None


class SpecialistCapabilityRegistry:
    def __init__(self):
        self.capabilities: dict[str, SpecialistCapability] = {}

    def register(self, capability: SpecialistCapability) -> None:
        if not capability.capability_id or not capability.schema_version or not capability.safety_policy_version:
            raise ValueError("SPECIALIST_CAPABILITY_INVALID")
        self.capabilities[capability.capability_id] = capability

    def release(self, capability_id: str, certificate_id: str) -> SpecialistCapability:
        current = self.capabilities.get(capability_id)
        if not current or not certificate_id:
            raise ValueError("SPECIALIST_CAPABILITY_NOT_FOUND")
        released = SpecialistCapability(**{**asdict(current), "status": "PUBLIC", "certificate_id": certificate_id})
        self.capabilities[capability_id] = released
        return released

    def resolve(self, capability_id: str) -> SpecialistCapability:
        capability = self.capabilities.get(capability_id)
        if not capability or capability.status != "PUBLIC":
            raise ValueError("SPECIALIST_CAPABILITY_NOT_AVAILABLE")
        return capability
