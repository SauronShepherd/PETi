from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()


def validate_smoke_payload(payload: object) -> ValidationResult:
    if not isinstance(payload, dict):
        return ValidationResult(False, ("OUTPUT_NOT_OBJECT",))
    errors = []
    if not isinstance(payload.get("summary"), str):
        errors.append("SUMMARY_REQUIRED")
    if not isinstance(payload.get("observations", []), list):
        errors.append("OBSERVATIONS_MUST_BE_LIST")
    return ValidationResult(not errors, tuple(errors))
