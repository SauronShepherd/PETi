import pytest
from app.agents.schemas import FecesAgentResultV1
from pydantic import ValidationError


def test_provider_schema_forbids_unknown_fields():
    with pytest.raises(ValidationError):
        FecesAgentResultV1(evidence_quality="HIGH", unexpected="tool")
