import json
from types import SimpleNamespace

import pytest
from app.ai.providers.gemini import GeminiApiKeyTransport, ProviderError, VertexGenAITransport


class Models:
    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(text='{"observations": []}', usage_metadata=SimpleNamespace(prompt_token_count=7, candidates_token_count=3))


def test_official_genai_transport_calls_sdk_and_returns_structured_json():
    models = Models()
    result = VertexGenAITransport("sandbox", "europe-west1", client=SimpleNamespace(models=models))({
        "model": "gemini-3.5-pro", "prompt": "observe",
        "media": [{"reference": "gs://bucket/object", "kind": "IMAGE", "mime_type": "image/jpeg"}],
    })
    assert result["payload"] == {"observations": []}
    assert result["usage"]["promptTokenCount"] == 7
    assert models.kwargs["model"] == "gemini-3.5-pro"
    parts = models.kwargs["contents"]
    assert parts[-1] == {"text": "observe"}
    media_part = parts[0]
    if isinstance(media_part, dict):
        assert media_part["file_data"] == {
            "file_uri": "gs://bucket/object", "mime_type": "image/jpeg"
        }
    else:
        blob = media_part.file_data
        assert blob.file_uri == "gs://bucket/object"
        assert blob.mime_type == "image/jpeg"


def test_api_key_transport_sends_inline_media(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self):
            return json.dumps({"candidates": [{"content": {"parts": [{"text": "{}"}]}}]}).encode()

    monkeypatch.setattr(
        "app.ai.providers.gemini.urlopen",
        lambda request, timeout: (captured.setdefault("body", json.loads(request.data)), Response())[1],
    )
    GeminiApiKeyTransport()(  # type: ignore[call-arg]
        {"model": "gemini-test", "prompt": "inspect", "media": [
            {"inline_data": b"image", "mime_type": "image/jpeg"},
        ]},
        "key",
    )
    parts = captured["body"]["contents"][0]["parts"]
    assert {"inline_data": {"mime_type": "image/jpeg", "data": "aW1hZ2U="}} in parts
    assert {"text": "inspect"} in parts


def test_api_key_transport_rejects_gcs_without_text_fallback():
    with pytest.raises(ProviderError, match="PROVIDER_MEDIA_SOURCE_UNSUPPORTED"):
        GeminiApiKeyTransport()(
            {"model": "gemini-test", "prompt": "inspect", "media": [
                {"reference": "gs://bucket/object", "mime_type": "image/jpeg"},
            ]},
            "key",
        )
