from types import SimpleNamespace

from app.ai.providers.gemini import VertexGenAITransport


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
