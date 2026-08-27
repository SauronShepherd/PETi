import pytest
from app.peti_check.contracts import PetiCheckResultV1


def test_observation_cannot_contain_interpretation_field():
    with pytest.raises(ValueError, match="observation_interpretation_mixing"):
        PetiCheckResultV1.from_payload(
            {"summary": "x", "observations": [{"text": "x", "interpretation": "y"}]}
        )


def test_interpretation_cannot_contain_observation_field():
    with pytest.raises(ValueError, match="interpretation_observation_mixing"):
        PetiCheckResultV1.from_payload(
            {"summary": "x", "possible_interpretations": [{"text": "x", "observation": "y"}]}
        )


def test_source_media_ids_are_typed_and_preserved():
    result = PetiCheckResultV1.from_payload(
        {"summary": "x", "source_media_ids": ["media-1", "media-2"]}
    )
    assert result.source_media_ids == ["media-1", "media-2"]
