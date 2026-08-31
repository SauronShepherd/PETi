from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ProviderInvocationResult:
    provider: str
    model_id: str
    provider_request_id: str | None
    structured_payload: dict
    usage: dict
    latency_ms: int | None = None
    finish_metadata: dict | None = None


class AgentModelProvider(Protocol):
    def invoke(self, *, role: str, model_binding: Any, prompt_version: str,
               context_bundle: Any, tool_declarations: list[Any],
               response_schema: Any, timeout_seconds: float) -> ProviderInvocationResult: ...
