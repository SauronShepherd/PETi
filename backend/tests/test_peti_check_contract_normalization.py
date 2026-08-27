import pytest
from app.peti_check.contracts import PetiCheckResultV1


def test_peti_check_payload_normalizes_to_typed_contract():
    result = PetiCheckResultV1.from_payload(
        {
            "summary": "Review the media",
            "observations": [{"text": "Repeated head shaking is visible", "confidence": "HIGH"}],
            "uncertainties": ["The cause cannot be determined from this media"],
            "possible_interpretations": ["Several explanations are possible"],
            "red_flags": [],
            "recommended_actions": ["Arrange veterinary review if it continues"],
            "limitations": ["This is not a diagnosis"],
            "evidence_quality": {"level": "MEDIUM"},
            "safety_state": "REVIEW",
        }
    )
    assert result.observations[0].confidence == "HIGH"
    assert result.safety_state == "REVIEW"
    assert result.evidence_quality.level == "PARTIAL"


def test_peti_check_contract_rejects_empty_observation():
    with pytest.raises(ValueError, match="observations"):
        PetiCheckResultV1.from_payload({"summary": "x", "observations": [{"text": ""}]})
