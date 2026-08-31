from __future__ import annotations

import logging
from typing import Any, Protocol

from app.agent_runtime.instrumentation import InvocationContext, current_invocation
from app.ai.preparation.core import PreparedMediaPackage

from .base import AIProvider, ProviderError, ProviderResponse

logger = logging.getLogger(__name__)


class ProviderTraceObserver(Protocol):
    def started(self, context: InvocationContext, provider: str, model: str) -> Any: ...
    def succeeded(self, context: InvocationContext, handle: Any, response: ProviderResponse) -> None: ...
    def failed(self, context: InvocationContext, handle: Any, error_code: str, retryable: bool) -> None: ...


class InstrumentedAIProvider:
    """Provider decorator that attributes model calls without recording prompts or content."""

    instrumented = True

    def __init__(self, delegate: AIProvider, observer: ProviderTraceObserver):
        self.delegate = delegate
        self.observer = observer
        self.name = delegate.name
        self.model = delegate.model
        self.capabilities = delegate.capabilities

    def analyze(self, media: PreparedMediaPackage, prompt: str, user_context: str | None = None) -> ProviderResponse:
        context = current_invocation()
        if context is None:
            return self.delegate.analyze(media, prompt, user_context)
        try:
            handle = self.observer.started(context, self.name, self.model)
        except Exception:  # noqa: BLE001 - tracing is explicitly fail-open
            logger.warning("provider_trace_start_failed", extra={"provider": self.name, "model": self.model})
            handle = None
        try:
            response = self.delegate.analyze(media, prompt, user_context)
            if handle is not None:
                try:
                    self.observer.succeeded(context, handle, response)
                except Exception:  # noqa: BLE001 - provider result remains authoritative
                    logger.warning("provider_trace_complete_failed", extra={"provider": self.name, "model": self.model})
            return response
        except ProviderError as exc:
            if handle is not None:
                try:
                    self.observer.failed(context, handle, exc.code, exc.retryable)
                except Exception:  # noqa: BLE001 - preserve original provider error
                    logger.warning("provider_trace_failure_write_failed", extra={"provider": self.name, "model": self.model, "error_code": exc.code})
            raise
        except Exception:
            if handle is not None:
                try:
                    self.observer.failed(context, handle, "UNEXPECTED_PROVIDER_ERROR", False)
                except Exception:  # noqa: BLE001 - preserve original provider error
                    logger.warning("provider_trace_failure_write_failed", extra={"provider": self.name, "model": self.model, "error_code": "UNEXPECTED_PROVIDER_ERROR"})
            raise


class LabProviderTraceObserver:
    def __init__(self, runs, tracing):
        self.runs = runs
        self.tracing = tracing

    def _run(self, context: InvocationContext):
        return self.runs.get(context.owner_user_id, context.run_id)

    def started(self, context: InvocationContext, provider: str, model: str):
        return self.tracing.start_model_call(self._run(context), step_id=context.step_id,
            agent_id=context.agent_id, provider=provider, model_id=model,
            prompt_version=context.prompt_version, schema_version=context.schema_version)

    def succeeded(self, context: InvocationContext, handle, response: ProviderResponse) -> None:
        self.tracing.complete_model_call(self._run(context), handle[0], handle[1], response)

    def failed(self, context: InvocationContext, handle, error_code: str, retryable: bool) -> None:
        self.tracing.fail_model_call(self._run(context), handle[0], handle[1],
            error_code=error_code, retryable=retryable)
