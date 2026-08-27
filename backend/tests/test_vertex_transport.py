import json

from app.ai.providers.gemini import VertexGeminiTransport


def test_vertex_transport_builds_structured_json_request(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return json.dumps(
                {"candidates": [{"content": {"parts": [{"text": json.dumps({"summary": "ok"})}]}}]}
            ).encode()

    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        return Response()

    monkeypatch.setattr("app.ai.providers.gemini.urlopen", fake_urlopen)
    result = VertexGeminiTransport("p", "europe-west1", lambda: "token")(
        {"model": "gemini-test", "prompt": "policy", "media": []}
    )
    assert result["payload"]["summary"] == "ok"
    assert captured["request"].headers["Authorization"] == "Bearer token"
