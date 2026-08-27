from dataclasses import dataclass
from typing import Protocol

from app.ai.preparation.core import PreparedMediaPackage


@dataclass(frozen=True)
class ProviderUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_input_tokens: int | None = None
    media_usage: dict | None = None
    provider_request_id: str | None = None
    latency_ms: int | None = None


@dataclass(frozen=True)
class ProviderCapabilities:
    media_types: frozenset[str]
    structured_json: bool = True
    max_media_items: int = 5


@dataclass(frozen=True)
class ProviderResponse:
    payload: dict
    usage: ProviderUsage
    provider: str
    model: str
    accepted: bool = True


class AIProvider(Protocol):
    name: str
    model: str
    capabilities: ProviderCapabilities

    def analyze(
        self, media: PreparedMediaPackage, prompt: str, user_context: str | None = None
    ) -> ProviderResponse: ...


class ProviderError(RuntimeError):
    def __init__(self, code: str, retryable: bool = False):
        super().__init__(code)
        self.code, self.retryable = code, retryable
