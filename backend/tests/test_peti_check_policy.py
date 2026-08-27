from app.peti_check.contracts import Observation, PetiCheckResultV1
from app.peti_check.guardrails import validate_peti_check
from app.safety.engine import evaluate_safety


def test_observation_and_diagnosis_are_separated():
    result = PetiCheckResultV1(
        "Review recommended", [Observation("The dog is diagnosed with otitis")]
    )
    assert "DIAGNOSIS_IN_OBSERVATION" in validate_peti_check(result)


def test_safety_engine_overrides_model_reassurance():
    decision = evaluate_safety(
        {"summary": "nothing to worry about"}, "The dog has difficulty breathing"
    )
    assert decision.state == "URGENT"
