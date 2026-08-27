import pytest
from app.ai.preparation.core import MediaPreparer
from app.ai.providers.base import ProviderError
from app.ai.providers.fake import FakeAIProvider
from app.services.ports import FakeScenario


def test_fake_provider_success_is_the_default():
    response = FakeAIProvider().analyze(MediaPreparer().prepare([{"id": "m", "kind": "image", "mime_type": "image/png", "reference": "gs://bucket/object"}]))
    assert response.accepted and response.payload["summary"]


@pytest.mark.parametrize("scenario,code", [
    (FakeScenario.TIMEOUT, "PROVIDER_TIMEOUT"),
    (FakeScenario.RATE_LIMIT, "PROVIDER_RATE_LIMITED"),
])
def test_fake_provider_reproduces_retryable_failures(scenario, code):
    with pytest.raises(ProviderError, match=code):
        FakeAIProvider(scenario).analyze(MediaPreparer().prepare([{"id": "m", "kind": "image", "mime_type": "image/png", "reference": "gs://bucket/object"}]))


def test_fake_provider_reproduces_malformed_and_safety_payloads():
    media = MediaPreparer().prepare([{"id": "m", "kind": "image", "mime_type": "image/png", "reference": "gs://bucket/object"}])
    assert "malformed" in FakeAIProvider(FakeScenario.MALFORMED_OUTPUT).analyze(media).payload
    assert "diagnosis" in FakeAIProvider(FakeScenario.SAFETY_VIOLATION).analyze(media).payload["summary"]
