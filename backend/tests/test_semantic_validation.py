import pytest
from app.agent_runtime.semantic_validation import deterministic_feces_safety, validate_longitudinal


def test_longitudinal_requires_comparability_before_change():
    with pytest.raises(ValueError, match="WITHOUT_COMPARABILITY"):
        validate_longitudinal({"comparability": "INSUFFICIENT_DATA", "change_label": "WORSENED"})


def test_feces_safety_is_deterministic_and_fail_closed():
    assert deterministic_feces_safety({"red_flags": ["COLLAPSE"]}) == "URGENT_VETERINARY_CONTACT"
    assert deterministic_feces_safety({"red_flags": []}) == "NORMAL_INFORMATION"
