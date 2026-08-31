from app.agent_runtime.structured_invocation import StructuredFailure, parse_with_bounded_repair
from app.agents.schemas import EvidenceIntakeResultV1


def test_structured_output_can_be_repaired_once():
    result = parse_with_bounded_repair({"evidence_quality": "HIGH"}, EvidenceIntakeResultV1, repair=lambda _: {"usable": True, "evidence_quality": "HIGH"})
    assert result.usable is True

def test_structured_output_repair_is_bounded():
    calls = []
    result = parse_with_bounded_repair({}, EvidenceIntakeResultV1, repair=lambda value: calls.append(value) or {}, max_attempts=1)
    assert isinstance(result, StructuredFailure) and len(calls) == 1
