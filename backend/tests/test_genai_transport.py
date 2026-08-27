from types import SimpleNamespace

from app.ai.providers.gemini import VertexGenAITransport


class Models:
    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(text='{"observations": []}', usage_metadata=SimpleNamespace(prompt_token_count=7, candidates_token_count=3))


def test_official_genai_transport_calls_sdk_and_returns_structured_json():
    models = Models()
    result = VertexGenAITransport("sandbox", "europe-west1", client=SimpleNamespace(models=models))({
        "model": "gemini-3.5-pro", "prompt": "observe", "media": [{"reference": "hash", "kind": "IMAGE"}],
    })
    assert result["payload"] == {"observations": []}
    assert result["usage"]["promptTokenCount"] == 7
    assert models.kwargs["model"] == "gemini-3.5-pro"
