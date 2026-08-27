import pytest
from app.ai.preparation.core import (
    AudioMediaPreparer,
    DocumentMediaPreparer,
    ImageMediaPreparer,
    MediaPreparer,
    VideoMediaPreparer,
)
from app.ai.providers.fake import FakeAIProvider
from app.ai.validation.core import validate_smoke_payload
from app.analysis.domain import AnalysisJob, AnalysisStatus
from app.analysis.repositories import (
    InMemoryAnalysisJobRepository,
    InMemoryAnalysisResultRepository,
)
from app.config.settings import Environment, Settings


def test_job_repository_rejects_illegal_transition():
    repo = InMemoryAnalysisJobRepository()
    job = AnalysisJob("j", "u", "a", "DOG", "PETI_CHECK", ["m"], "k", "r", "f")
    repo.save(job)
    with pytest.raises(ValueError, match="ILLEGAL_ANALYSIS_TRANSITION"):
        repo.transition("j", AnalysisStatus.COMPLETED)


def test_result_repository_is_immutable_per_job():
    from app.analysis.domain import AnalysisResult

    repo = InMemoryAnalysisResultRepository()
    result = AnalysisResult(
        "r",
        "j",
        "u",
        "a",
        "PETI_CHECK",
        "peti_check",
        "1.0.0",
        {},
        "VALID",
        "PASS",
        "CLEAR",
        [],
        "FAKE",
        "m",
        "1",
        "1",
        "1",
        "1",
        "DOG-v1",
        {},
        {},
    )
    repo.save(result)
    replacement = AnalysisResult(
        "r2",
        "j",
        "u",
        "a",
        "PETI_CHECK",
        "peti_check",
        "1.0.0",
        {},
        "VALID",
        "PASS",
        "CLEAR",
        [],
        "FAKE",
        "m",
        "1",
        "1",
        "1",
        "1",
        "DOG-v1",
        {},
        {},
    )
    with pytest.raises(ValueError, match="IMMUTABLE"):
        repo.save(replacement)


def test_provider_output_boundary_and_preparation():
    package = MediaPreparer().prepare([{"id": "m1", "kind": "image"}])
    response = FakeAIProvider().analyze(package)
    assert validate_smoke_payload(response.payload).valid


def test_preparation_dispatches_each_modality_to_named_boundary():
    preparer = MediaPreparer()
    package = preparer.prepare([
        {"id": "image", "kind": "IMAGE"},
        {"id": "video", "kind": "VIDEO"},
        {"id": "audio", "kind": "AUDIO"},
        {"id": "document", "kind": "DOCUMENT"},
    ])
    assert [item.kind for item in package.items] == [
        ImageMediaPreparer.kind, VideoMediaPreparer.kind,
        AudioMediaPreparer.kind, DocumentMediaPreparer.kind,
    ]


def test_provider_exposes_explicit_media_capabilities():
    capabilities = FakeAIProvider.capabilities
    assert capabilities.structured_json
    assert "IMAGE" in capabilities.media_types
    assert capabilities.max_media_items == 5


def test_non_local_requires_cloud_task_configuration_and_production_provider():
    with pytest.raises(ValueError, match="tasks_project_id"):
        Settings(
            environment=Environment.DEV, auth_mode="FIREBASE", media_bucket="bucket"
        ).validate_startup()


def test_non_local_worker_does_not_require_self_worker_url():
    Settings(
        environment=Environment.DEV,
        service="peti-worker",
        auth_mode="FIREBASE",
        media_bucket="bucket",
        tasks_project_id="p",
    ).validate_startup()
    with pytest.raises(ValueError, match="FAKE"):
        Settings(
            environment=Environment.PRODUCTION,
            auth_mode="FIREBASE",
                project_id="p",
                media_bucket="b",
                tasks_project_id="p",
                storage_mode="FIRESTORE",
                analysis_worker_url="https://worker",
        ).validate_startup()
