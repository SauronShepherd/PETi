from dataclasses import dataclass


@dataclass(frozen=True)
class CaptureProtocol:
    capability_id: str
    required_media: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    humane_capture_required: bool = True


@dataclass(frozen=True)
class SpecialistSafetyPolicy:
    capability_id: str
    prohibited_claims: tuple[str, ...]
    urgent_copy: str
    version: str = "1.0.0"


@dataclass(frozen=True)
class SpecialistReleaseCertificate:
    capability_id: str
    schema_version: str
    guardrail_version: str
    safety_policy_version: str
    evaluation_manifest: str
    status: str = "PUBLIC"


class WeeklyReportSectionBuilder:
    def __init__(self, section_type): self.section_type = section_type
    def build(self, evidence_bundle):
        return {"section_type": self.section_type, "state": "EVIDENCE_AVAILABLE" if evidence_bundle else "NOT_ENOUGH_DATA", "source_references": list(evidence_bundle)}
