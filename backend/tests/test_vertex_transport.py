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


def test_vertex_transport_sends_gcs_and_inline_media_as_real_parts(monkeypatch):
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self):
            return json.dumps({"candidates": [{"content": {"parts": [{"text": "{}"}]}}]}).encode()

    captured = {}
    monkeypatch.setattr(
        "app.ai.providers.gemini.urlopen",
        lambda request, timeout: (captured.setdefault("body", json.loads(request.data)), Response())[1],
    )
    VertexGeminiTransport("p", "europe-west1", lambda: "token")({
        "model": "gemini-test", "prompt": "inspect", "media": [
            {"reference": "gs://bucket/image", "mime_type": "image/jpeg"},
            {"inline_data": b"video", "mime_type": "video/mp4"},
            {"inline_data": "YXVkaW8=", "mime_type": "audio/mpeg"},
        ],
    })
    parts = captured["body"]["contents"][0]["parts"]
    assert {"fileData": {"fileUri": "gs://bucket/image", "mimeType": "image/jpeg"}} in parts
    assert {"inlineData": {"mimeType": "video/mp4", "data": "dmlkZW8="}} in parts
    assert {"inlineData": {"mimeType": "audio/mpeg", "data": "YXVkaW8="}} in parts
    assert {"text": "inspect"} in parts
