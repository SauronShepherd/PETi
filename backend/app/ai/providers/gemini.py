import base64
import json
import threading
import time
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

from app.ai.preparation.core import PreparedMediaPackage

from .base import ProviderCapabilities, ProviderError, ProviderResponse, ProviderUsage


def _usage_value(usage: dict[str, Any], *names: str) -> int | None:
    for name in names:
        value = usage.get(name)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
    return None


class GeminiProvider:
    """Gemini adapter with an injectable transport; credentials stay outside domain code."""

    name = "GEMINI"

    def __init__(self, model: str, transport, config_version: str = "1.0.0", api_keys=None, max_attempts: int = 3, backoff_seconds: float = 0.25):
        self.model, self.transport, self.config_version = model, transport, config_version
        self.api_keys = api_keys
        self.max_attempts = max(1, max_attempts)
        self.backoff_seconds = max(0.0, backoff_seconds)
        self.capabilities = ProviderCapabilities(frozenset({"IMAGE", "VIDEO", "AUDIO"}))

    def analyze(
        self, media: PreparedMediaPackage, prompt: str, user_context: str | None = None
    ) -> ProviderResponse:
        started = time.perf_counter()
        request = {
            "model": self.model,
            "prompt": prompt,
            "context": user_context,
            "media": [
                {"id": x.asset_id, "kind": x.kind.value, "reference": x.reference}
                for x in media.items
            ],
            "response_mime_type": "application/json",
        }
        try:
            raw = None
            attempts = min(self.max_attempts, len(self.api_keys) if self.api_keys else 1)
            for attempt in range(attempts):
                try:
                    key = self.api_keys.acquire_key() if self.api_keys else None
                    raw = self.transport(request, key) if self.api_keys else self.transport(request)
                    break
                except Exception as exc:
                    retryable = isinstance(exc, ProviderError) and exc.retryable or (
                        isinstance(exc, (TimeoutError, HTTPError)) and (
                        not isinstance(exc, HTTPError) or exc.code == 429 or exc.code >= 500
                        )
                    )
                    if not retryable or attempt == attempts - 1:
                        raise
                    time.sleep(self.backoff_seconds * (2**attempt))
            if raw is None:
                raise ProviderError("PROVIDER_REQUEST_FAILED", True)
            payload = raw.get("payload", raw) if isinstance(raw, dict) else raw
            usage = raw.get("usage", {}) if isinstance(raw, dict) else {}
            return ProviderResponse(
                payload,
                ProviderUsage(
                    _usage_value(usage, "input_tokens", "promptTokenCount", "prompt_token_count"),
                    _usage_value(usage, "output_tokens", "candidatesTokenCount", "candidate_token_count"),
                    _usage_value(usage, "cached_input_tokens", "cachedContentTokenCount", "cached_content_token_count"),
                    usage.get("media_usage"),
                    usage.get("provider_request_id", usage.get("requestId", str(uuid4()))),
                    round((time.perf_counter() - started) * 1000),
                ),
                self.name,
                self.model,
            )
        except TimeoutError as exc:
            raise ProviderError("PROVIDER_TIMEOUT", True) from exc
        except ProviderError:
            raise
        except HTTPError as exc:
            if exc.code == 429:
                raise ProviderError("PROVIDER_RATE_LIMITED", True) from exc
            if exc.code >= 500:
                raise ProviderError("PROVIDER_UNAVAILABLE", True) from exc
            raise ProviderError("PROVIDER_REQUEST_FAILED", False) from exc
        except Exception as exc:
            raise ProviderError("PROVIDER_REQUEST_FAILED", False) from exc


class GeminiApiKeyPool:
    """Thread-safe UTC-day quota and round-robin pool; secrets never appear in errors."""

    def __init__(self, comma_separated_keys: str, daily_limit_per_key: int = 20):
        keys = [key.strip() for key in comma_separated_keys.split(",") if key.strip()]
        self._keys = tuple(dict.fromkeys(keys))
        if not self._keys:
            raise ValueError("PETI_GEMINI_API_KEYS must contain at least one key")
        if daily_limit_per_key <= 0:
            raise ValueError("daily_limit_per_key must be positive")
        self._daily_limit = daily_limit_per_key
        self._day = datetime.now(UTC).date()
        self._used = [0] * len(self._keys)
        self._index = 0
        self._lock = threading.Lock()

    def __len__(self):
        return len(self._keys)

    def next_key(self) -> str:
        with self._lock:
            key = self._keys[self._index]
            self._index = (self._index + 1) % len(self._keys)
            return key

    def acquire_key(self) -> str:
        with self._lock:
            today = datetime.now(UTC).date()
            if today != self._day:
                self._day, self._used = today, [0] * len(self._keys)
            for offset in range(len(self._keys)):
                index = (self._index + offset) % len(self._keys)
                if self._used[index] < self._daily_limit:
                    self._index = (index + 1) % len(self._keys)
                    self._used[index] += 1
                    return self._keys[index]
        raise ProviderError("GEMINI_DAILY_QUOTA_EXHAUSTED", True)


class GeminiApiKeyTransport:
    """Google AI Studio REST transport; callers must supply a key pool at runtime."""

    def __init__(self, timeout_seconds: int = 90, endpoint: str = "https://generativelanguage.googleapis.com/v1beta/models"):
        self.timeout_seconds, self.endpoint = timeout_seconds, endpoint.rstrip("/")

    def __call__(self, request: dict[str, Any], api_key: str) -> dict[str, Any]:
        body = {"contents": [{"parts": [{"text": request["prompt"]}]}], "generationConfig": {"responseMimeType": "application/json"}}
        url = f"{self.endpoint}/{request['model']}:generateContent?key={api_key}"
        http = Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(http, timeout=self.timeout_seconds) as response:
            data = json.loads(response.read())
        candidate = data["candidates"][0]["content"]["parts"][0]["text"]
        return {"payload": json.loads(candidate), "usage": data.get("usageMetadata", {})}


class VertexGeminiTransport:
    """Minimal Vertex AI transport; credentials are supplied by the runtime."""

    def __init__(self, project_id: str, location: str, token_provider, timeout_seconds: int = 90):
        self.endpoint = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models"
        self.token_provider = token_provider
        self.timeout_seconds = timeout_seconds

    def __call__(self, request: dict[str, Any]) -> dict[str, Any]:
        model = request["model"]
        body: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": request["prompt"]}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        contents: list[dict[str, Any]] = body["contents"]
        parts: list[dict[str, Any]] = contents[0]["parts"]
        for item in request.get("media", []):
            mime_type = item.get("mime_type")
            if not isinstance(mime_type, str) or "/" not in mime_type:
                raise ProviderError("PROVIDER_MEDIA_MIME_INVALID", False)
            reference = item.get("reference")
            if isinstance(reference, str) and reference.startswith("gs://"):
                parts.append({"fileData": {"fileUri": reference, "mimeType": mime_type}})
                continue
            inline_data = item.get("inline_data")
            if isinstance(inline_data, bytes):
                inline_data = base64.b64encode(inline_data).decode("ascii")
            if isinstance(inline_data, str) and inline_data:
                parts.append({"inlineData": {"mimeType": mime_type, "data": inline_data}})
                continue
            raise ProviderError("PROVIDER_MEDIA_SOURCE_INVALID", False)
        if request.get("context"):
            parts.append({"text": f"Owner context: {request['context']}"})
        url = f"{self.endpoint}/{model}:generateContent"
        http = Request(
            url,
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {self.token_provider()}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(http, timeout=self.timeout_seconds) as response:
            data = json.loads(response.read())
        candidate = data["candidates"][0]["content"]["parts"][0]["text"]
        return {"payload": json.loads(candidate), "usage": data.get("usageMetadata", {})}


class VertexGenAITransport:
    """Vertex transport backed by Google's official ``google-genai`` SDK.

    The SDK is imported lazily so LOCAL/fake environments remain zero-cost and
    do not need cloud credentials. A client may be injected for contract tests.
    """

    def __init__(self, project_id: str, location: str, *, client=None, timeout_seconds: int = 90):
        self.project_id, self.location, self.client, self.timeout_seconds = project_id, location, client, timeout_seconds

    def _client(self):
        if self.client is not None:
            return self.client
        from google import genai  # type: ignore[import-not-found]

        self.client = genai.Client(vertexai=True, project=self.project_id, location=self.location,
                                   http_options={"timeout": self.timeout_seconds * 1000})
        return self.client

    def __call__(self, request: dict[str, Any]) -> dict[str, Any]:
        client = self._client()
        config: Any = None
        try:
            from google.genai import types  # type: ignore[import-not-found]
            config = types.GenerateContentConfig(response_mime_type="application/json")
        except ImportError:
            config = {"response_mime_type": "application/json"}
        media_parts = []
        for item in request.get("media", []):
            reference = item.get("reference")
            mime_type = item.get("mime_type")
            if not isinstance(reference, str) or not reference.startswith("gs://"):
                raise ProviderError("PROVIDER_MEDIA_SOURCE_INVALID", False)
            if not isinstance(mime_type, str) or "/" not in mime_type:
                raise ProviderError("PROVIDER_MEDIA_MIME_INVALID", False)
            try:
                media_parts.append(types.Part.from_uri(file_uri=reference, mime_type=mime_type))
            except NameError:
                media_parts.append({"file_data": {"file_uri": reference, "mime_type": mime_type}})
        contents = media_parts + [{"text": request["prompt"]}]
        if request.get("context"):
            contents.append({"text": f"Owner context: {request['context']}"})
        response = client.models.generate_content(model=request["model"], contents=contents, config=config)
        text = getattr(response, "text", None)
        if not text:
            raise ProviderError("PROVIDER_EMPTY_RESPONSE", True)
        usage = getattr(response, "usage_metadata", None)
        usage_dict = {
            "promptTokenCount": getattr(usage, "prompt_token_count", None),
            "candidatesTokenCount": getattr(usage, "candidates_token_count", None),
        }
        return {"payload": json.loads(text), "usage": usage_dict}
