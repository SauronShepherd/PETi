from dataclasses import dataclass

from app.peti_check.contracts import PetiCheckResultV1
from app.peti_check.guardrails import validate_peti_check


@dataclass(frozen=True)
class GuardrailResult:
    passed: bool
    violations: tuple[str, ...] = ()


def apply_guardrails(result: PetiCheckResultV1) -> GuardrailResult:
    violations = tuple(validate_peti_check(result))
    return GuardrailResult(not violations, violations)
