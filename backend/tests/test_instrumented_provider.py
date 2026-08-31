from dataclasses import dataclass

import pytest
from app.agent_runtime.instrumentation import (
    InvocationContext,
    current_invocation,
    invocation_scope,
)
from app.ai.providers.fake import FakeAIProvider
from app.ai.providers.instrumented import InstrumentedAIProvider
from app.services.ports import FakeScenario


class Media:
    def __init__(self):
        self.items = []


@dataclass
class Observer:
    started_count: int = 0
    success_count: int = 0
    failure_count: int = 0

    def started(self, context, provider, model):
        self.started_count += 1
        assert context.step_id == "step-1" and provider == "FAKE"
        return "handle"

    def succeeded(self, context, handle, response):
        self.success_count += 1
        assert handle == "handle" and response.model == "fake-platform-smoke-v1"

    def failed(self, context, handle, error_code, retryable):
        self.failure_count += 1


def context():
    return InvocationContext("owner", "run", "step-1", "agent", "corr", "deploy")


def test_provider_instrumentation_is_context_scoped_and_content_blind():
    observer = Observer(); provider = InstrumentedAIProvider(FakeAIProvider(), observer)
    with invocation_scope(context()):
        provider.analyze(Media(), "private prompt", "private context")
        assert current_invocation() is not None
    assert current_invocation() is None
    assert (observer.started_count, observer.success_count, observer.failure_count) == (1, 1, 0)


def test_provider_instrumentation_records_sanitized_failure_and_no_context_is_noop():
    observer = Observer(); provider = InstrumentedAIProvider(FakeAIProvider(FakeScenario.TIMEOUT), observer)
    with pytest.raises(Exception, match="PROVIDER_TIMEOUT"), invocation_scope(context()):
        provider.analyze(Media(), "secret")
    assert observer.failure_count == 1
    plain = Observer(); InstrumentedAIProvider(FakeAIProvider(), plain).analyze(Media(), "secret")
    assert plain.started_count == 0
