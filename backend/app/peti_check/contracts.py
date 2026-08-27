from dataclasses import dataclass, field
from typing import Literal, cast

SafetyState = Literal["CLEAR", "REVIEW", "URGENT", "INSUFFICIENT_EVIDENCE"]


@dataclass(frozen=True)
class EvidenceQuality:
    level: Literal["GOOD", "PARTIAL", "INSUFFICIENT"]
    limitations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Observation:
    text: str
    provenance: Literal["VISIBLE", "AUDIBLE", "USER_REPORTED"] = "VISIBLE"
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"


@dataclass(frozen=True)
class Uncertainty:
    text: str


@dataclass(frozen=True)
class Interpretation:
    text: str
    non_diagnostic: bool = True


@dataclass(frozen=True)
class RedFlag:
    text: str
    urgency: Literal["SOON", "URGENT"] = "SOON"


@dataclass(frozen=True)
class RecommendedAction:
    text: str


@dataclass
class PetiCheckResultV1:
    summary: str
    observations: list[Observation] = field(default_factory=list)
    uncertainties: list[Uncertainty] = field(default_factory=list)
    possible_interpretations: list[Interpretation] = field(default_factory=list)
    red_flags: list[RedFlag] = field(default_factory=list)
    recommended_actions: list[RecommendedAction] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    evidence_quality: EvidenceQuality = field(default_factory=lambda: EvidenceQuality("INSUFFICIENT"))
    safety_state: SafetyState = "CLEAR"
    source_media_ids: list[str] = field(default_factory=list)
    schema_id: str = "peti_check"
    schema_version: str = "1.0.0"

    def to_dict(self) -> dict:
        from dataclasses import asdict

        return asdict(self)

    @classmethod
    def from_payload(cls, payload: dict) -> "PetiCheckResultV1":
        def text_items(key: str) -> list[str]:
            values = payload.get(key, [])
            if not isinstance(values, list):
                raise TypeError(f"PETI_CHECK_SCHEMA_INVALID:{key}")
            return [item if isinstance(item, str) else item.get("text", "") for item in values]

        evidence = payload.get("evidence_quality", {})
        if isinstance(evidence, str):
            evidence = {"level": evidence}
        level = evidence.get("level", "INSUFFICIENT") if isinstance(evidence, dict) else "INSUFFICIENT"
        level = {"HIGH": "GOOD", "MEDIUM": "PARTIAL", "LOW": "INSUFFICIENT"}.get(level, level)
        if level not in {"GOOD", "PARTIAL", "INSUFFICIENT"}:
            raise ValueError("PETI_CHECK_SCHEMA_INVALID:evidence_quality")
        safety = payload.get("safety_state", "CLEAR")
        if safety not in {"CLEAR", "REVIEW", "URGENT", "INSUFFICIENT_EVIDENCE"}:
            safety = "REVIEW"
        observations = [
            Observation(
                item.get("text", "") if isinstance(item, dict) else item,
                item.get("provenance", "VISIBLE") if isinstance(item, dict) else "VISIBLE",
                item.get("confidence", "MEDIUM") if isinstance(item, dict) else "MEDIUM",
            )
            for item in payload.get("observations", [])
        ]
        if any(isinstance(item, dict) and "interpretation" in item for item in payload.get("observations", [])):
            raise ValueError("PETI_CHECK_SCHEMA_INVALID:observation_interpretation_mixing")
        if any(
            isinstance(item, dict) and "observation" in item
            for item in payload.get("possible_interpretations", [])
        ):
            raise ValueError("PETI_CHECK_SCHEMA_INVALID:interpretation_observation_mixing")
        if not all(item.text for item in observations):
            raise ValueError("PETI_CHECK_SCHEMA_INVALID:observations")
        source_media_ids = payload.get("source_media_ids", [])
        if not isinstance(source_media_ids, list) or not all(
            isinstance(item, str) and item for item in source_media_ids
        ):
            raise ValueError("PETI_CHECK_SCHEMA_INVALID:source_media_ids")
        return cls(
            summary=payload.get("summary", ""),
            observations=observations,
            uncertainties=[Uncertainty(x) for x in text_items("uncertainties")],
            possible_interpretations=[
                Interpretation(x) for x in text_items("possible_interpretations")
            ],
            red_flags=[RedFlag(x) for x in text_items("red_flags")],
            recommended_actions=[RecommendedAction(x) for x in text_items("recommended_actions")],
            limitations=text_items("limitations"),
            evidence_quality=EvidenceQuality(
                cast(Literal["GOOD", "PARTIAL", "INSUFFICIENT"], level),
                evidence.get("limitations", []) if isinstance(evidence, dict) else [],
            ),
            safety_state=safety,
            source_media_ids=source_media_ids,
        )
