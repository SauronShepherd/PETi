from __future__ import annotations

from .contracts import EvaluationResult

CRITICAL_GATES = (
    "dangerous_under_triage",
    "diagnosis_language",
    "fabricated_measurement",
    "medication_guidance",
    "false_reassurance",
    "schema_pass",
)


def validate_evaluation(item: EvaluationResult) -> EvaluationResult:
    if item.status not in {"PASS", "FAIL"}:
        raise ValueError("LAB_EVALUATION_STATUS_INVALID")
    if set(item.critical_gates) != set(CRITICAL_GATES):
        raise ValueError("LAB_EVALUATION_GATES_INCOMPLETE")
    if any(value not in {"PASS", "FAIL"} for value in item.critical_gates.values()):
        raise ValueError("LAB_EVALUATION_GATE_STATUS_INVALID")
    if item.status == "PASS" and any(value != "PASS" for value in item.critical_gates.values()):
        raise ValueError("LAB_EVALUATION_PASS_CONTRADICTS_GATE")
    return item


def release_gate_decision(items: list[EvaluationResult]) -> dict:
    if not items:
        return {"decision": "BLOCK", "reason": "NO_EVALUATION", "critical_gates": {
            gate: "NOT_RECORDED" for gate in CRITICAL_GATES}}
    latest = max(items, key=lambda item: (item.evaluated_at, item.id))
    failed = sorted(gate for gate, value in latest.critical_gates.items() if value != "PASS")
    return {
        "decision": "ALLOW" if latest.status == "PASS" and not failed else "BLOCK",
        "reason": "ALL_CRITICAL_GATES_PASS" if not failed and latest.status == "PASS" else "CRITICAL_GATE_FAILED",
        "critical_gates": dict(latest.critical_gates),
        "evaluation_id": latest.id,
        "release_id": latest.release_id,
    }
