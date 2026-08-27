from app.ai.providers.gemini import GeminiProvider


def test_gemini_adapter_exposes_immutable_configuration_version():
    provider = GeminiProvider("gemini-test", lambda request: {"payload": {}, "usage": {}}, "cfg-2")
    assert provider.config_version == "cfg-2"
