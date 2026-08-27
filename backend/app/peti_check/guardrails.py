import re

from .contracts import PetiCheckResultV1

DIAGNOSIS = re.compile(r"\b(has|diagnosed with|is suffering from|definitely)\s+[a-z][\w -]+", re.IGNORECASE)
MEASUREMENT = re.compile(r"\b\d+(?:\.\d+)?\s*°?\s*(?:c|f|degrees|kg|lb|bpm)\b", re.IGNORECASE)
MEDICATION = re.compile(r"\b(?:give|dose|dosage|mg|ml)\b", re.IGNORECASE)
FALSE_REASSURANCE = re.compile(
    r"\b(?:nothing to worry|definitely fine|no need to see a vet)\b", re.IGNORECASE
)
EXCESSIVE_CERTAINTY = re.compile(
    r"\b(?:definitely|certainly|conclusive(?:ly)?|confirmed|100\s*%)\b", re.IGNORECASE
)
SPECIALIST_LEAKAGE = re.compile(
    r"\b(?:periodontal\s+stage|pocket\s+depth|pulp\s+vitality|root\s+damage|bone\s+loss|"
    r"abscess|parasite(?:s)?|giardia|worm\s+species)\b",
    re.IGNORECASE,
)


def validate_peti_check(result: PetiCheckResultV1) -> list[str]:
    errors = validate_payload_text(result.to_dict())
    if any(DIAGNOSIS.search(item.text) for item in result.observations):
        errors.append("DIAGNOSIS_IN_OBSERVATION")
    return sorted(set(errors))


def sanitize_context(context: str | None, max_length: int = 500) -> str | None:
    if not context:
        return None
    return " ".join(context.strip().split())[:max_length]


def validate_payload_text(payload: object) -> list[str]:
    """Scan every model-visible string, including nested arrays/objects."""
    texts: list[str] = []

    def collect(value):
        if isinstance(value, str):
            texts.append(value)
        elif isinstance(value, dict):
            for child in value.values():
                collect(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)

    collect(payload)
    errors = []
    if any(DIAGNOSIS.search(x) for x in texts):
        errors.append("DIAGNOSIS_LANGUAGE")
    if any(MEASUREMENT.search(x) for x in texts):
        errors.append("FABRICATED_MEASUREMENT")
    if any(MEDICATION.search(x) for x in texts):
        errors.append("MEDICATION_GUIDANCE")
    if any(FALSE_REASSURANCE.search(x) for x in texts):
        errors.append("FALSE_REASSURANCE")
    if any(SPECIALIST_LEAKAGE.search(x) for x in texts):
        errors.append("SPECIALIST_LANGUAGE_LEAKAGE")
    quality = None
    if isinstance(payload, dict):
        evidence = payload.get("evidence_quality")
        if isinstance(evidence, dict):
            quality = evidence.get("level")
        elif isinstance(evidence, str):
            quality = evidence
    if str(quality).upper() in {"MEDIUM", "LOW", "PARTIAL", "INSUFFICIENT"} and any(
        EXCESSIVE_CERTAINTY.search(x) for x in texts
    ):
        errors.append("EXCESSIVE_CERTAINTY_FOR_EVIDENCE")
    return sorted(set(errors))
