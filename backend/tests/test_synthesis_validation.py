import pytest
from app.agent_runtime.semantic_validation import validate_synthesis


def test_synthesis_rejects_ungrounded_claims():
    with pytest.raises(ValueError, match="NOT_GROUNDED"):
        validate_synthesis([{"text": "unsupported", "evidence_ids": []}], "NORMAL_INFORMATION")


def test_synthesis_accepts_grounded_claims_and_known_safety():
    assert validate_synthesis([{"text": "observed", "evidence_ids": ["asset-1"]}], "PROMPT_VETERINARY_CONTACT")
