from uuid import uuid4

from app.ai.preparation.core import PreparedMediaPackage
from app.services.ports import FakeScenario

from .base import ProviderCapabilities, ProviderError, ProviderResponse, ProviderUsage


class FakeAIProvider:
    def __init__(self, scenario: FakeScenario = FakeScenario.SUCCESS):
        self.scenario = FakeScenario(scenario)

    name = "FAKE"
    model = "fake-platform-smoke-v1"
    capabilities = ProviderCapabilities(frozenset({"IMAGE", "VIDEO", "AUDIO"}))

    def analyze(
        self, media: PreparedMediaPackage, prompt: str = "", user_context: str | None = None
    ) -> ProviderResponse:
        if self.scenario is FakeScenario.TIMEOUT:
            raise ProviderError("PROVIDER_TIMEOUT", retryable=True)
        if self.scenario is FakeScenario.RATE_LIMIT:
            raise ProviderError("PROVIDER_RATE_LIMITED", retryable=True)
        if self.scenario is FakeScenario.MALFORMED_OUTPUT:
            return ProviderResponse({"malformed": True}, ProviderUsage(provider_request_id=str(uuid4())), self.name, self.model)
        if self.scenario is FakeScenario.SAFETY_VIOLATION:
            return ProviderResponse({"summary": "This is a diagnosis and prescription."}, ProviderUsage(provider_request_id=str(uuid4())), self.name, self.model)
        return ProviderResponse(
            {
                "summary": "Media was received for review.",
                "observations": [{"text": "Media is available for inspection."}],
                "evidence_quality": "MEDIUM",
            },
            ProviderUsage(12, 18, provider_request_id=str(uuid4()), latency_ms=1),
            self.name,
            self.model,
        )
