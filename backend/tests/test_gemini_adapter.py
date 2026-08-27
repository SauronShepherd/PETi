from urllib.error import HTTPError

import pytest

from app.ai.preparation.core import MediaPreparer
from app.ai.providers.base import ProviderError
from app.ai.providers.gemini import GeminiApiKeyPool, GeminiProvider, VertexGeminiTransport


def test_gemini_adapter_normalizes_structured_response_and_usage():
    seen = {}

    def transport(request):
        seen.update(request)
        return {"payload": {"summary": "ok"}, "usage": {"input_tokens": 10, "output_tokens": 4}}

    result = GeminiProvider("gemini-test", transport).analyze(
        MediaPreparer().prepare([{"id": "m", "kind": "image", "mime_type": "image/png", "reference": "gs://bucket/object"}]), "policy"
    )
    assert result.provider == "GEMINI"
    assert result.usage.input_tokens == 10
    assert seen["response_mime_type"] == "application/json"


def test_gemini_provider_rejects_raw_media_alternatives():
    provider = GeminiProvider("gemini-test", lambda _request: {"payload": {}, "usage": {}})
    for raw_media in (["asset-1"], [{"id": "asset-1", "reference": "gs://bucket/object"}], "gs://bucket/object"):
        with pytest.raises(ProviderError, match="PROVIDER_MEDIA_PACKAGE_REQUIRED"):
            provider.analyze(raw_media, "policy")


def test_gemini_capabilities_are_inherited_from_transport():
    provider = GeminiProvider("gemini-test", VertexGeminiTransport("p", "loc", lambda: "token"))
    assert provider.capabilities.media_types == frozenset({"IMAGE", "VIDEO", "AUDIO"})
    provider = GeminiProvider("gemini-test", GeminiApiKeyPool)  # unknown transport is fail-closed
    assert provider.capabilities.media_types == frozenset()


def test_gemini_adapter_normalizes_vertex_usage_metadata_names():
    def transport(_request):
        return {
            "payload": {"summary": "ok"},
            "usage": {"promptTokenCount": 21, "candidatesTokenCount": 8, "cachedContentTokenCount": 3, "requestId": "req-1"},
        }

    result = GeminiProvider("gemini-test", transport).analyze(
        MediaPreparer().prepare([{"id": "m", "kind": "image", "mime_type": "image/png", "reference": "gs://bucket/object"}]), "policy"
    )
    assert result.usage.input_tokens == 21
    assert result.usage.output_tokens == 8
    assert result.usage.cached_input_tokens == 3
    assert result.usage.provider_request_id == "req-1"


def test_gemini_keys_round_robin_and_retry_fallback():
    pool = GeminiApiKeyPool(" first , second,first, third ")
    seen = []

    def transport(request, key):
        seen.append(key)
        if key == "first":
            raise TimeoutError()
        return {"payload": {"summary": "ok"}, "usage": {}}

    result = GeminiProvider("gemini-test", transport, api_keys=pool, max_attempts=2).analyze(
        MediaPreparer().prepare([{"id": "m", "kind": "image", "mime_type": "image/png", "reference": "gs://bucket/object"}]), "policy"
    )
    assert result.payload["summary"] == "ok"
    assert seen == ["first", "second"]
    assert pool.next_key() == "third"


def test_gemini_daily_quota_skips_exhausted_key():
    pool = GeminiApiKeyPool("first,second", daily_limit_per_key=1)
    assert pool.acquire_key() == "first"
    assert pool.acquire_key() == "second"
    try:
        pool.acquire_key()
    except Exception as exc:  # noqa: BLE001
        assert str(exc) == "GEMINI_DAILY_QUOTA_EXHAUSTED"
    else:
        raise AssertionError("quota should be exhausted")


def test_gemini_provider_normalizes_rate_limit_and_server_errors():
    prepared = MediaPreparer().prepare([{"id": "m", "kind": "image", "mime_type": "image/png", "reference": "gs://bucket/object"}])
    for status, expected, retryable in (
        (429, "PROVIDER_RATE_LIMITED", True),
        (503, "PROVIDER_UNAVAILABLE", True),
        (400, "PROVIDER_REQUEST_FAILED", False),
    ):
        def transport(_request, code=status):
            raise HTTPError("https://example.test", code, "failure", {}, None)
        try:
            GeminiProvider("gemini-test", transport).analyze(prepared, "policy")
        except ProviderError as exc:
            assert exc.code == expected and exc.retryable is retryable
        else:
            raise AssertionError("provider error should be normalized")


def test_gemini_provider_preserves_canonical_provider_errors():
    def transport(_request):
        raise ProviderError("PROVIDER_RATE_LIMITED", True)
    try:
        GeminiProvider("gemini-test", transport).analyze(
                MediaPreparer().prepare([{"id": "m", "kind": "image", "mime_type": "image/png", "reference": "gs://bucket/object"}]), "policy"
        )
    except ProviderError as exc:
        assert exc.code == "PROVIDER_RATE_LIMITED"
    else:
        raise AssertionError("provider error should be preserved")
