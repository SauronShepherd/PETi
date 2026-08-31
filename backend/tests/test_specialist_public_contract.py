import pytest
from app.api.models.specialists import SpecialistCreateRequest, SpecialistWorkerCompletion
from pydantic import ValidationError


def test_public_specialist_request_rejects_provider_authority_fields():
    with pytest.raises(ValidationError):
        SpecialistCreateRequest(media_asset_ids=["media-1"], result={"observations": []})
    with pytest.raises(ValidationError):
        SpecialistCreateRequest(media_asset_ids=["media-1"], candidates=[{"field_type": "COAT_COLOR"}])


def test_worker_completion_is_separate_and_requires_trusted_identity():
    with pytest.raises(ValidationError):
        SpecialistWorkerCompletion(analysis_id="a", result={})
