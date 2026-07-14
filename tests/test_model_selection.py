from dove.model_clients import chat, list_ollama_models
from dove.schemas import ModelConfig


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_ollama_model_discovery(monkeypatch):
    captured = {}

    def fake_get(url, timeout):
        captured.update(url=url, timeout=timeout)
        return FakeResponse({"models": [{"name": "model-a"}, {"name": "model-b"}]})

    monkeypatch.setattr("dove.model_clients.requests.get", fake_get)
    models = list_ollama_models("http://localhost:11434/")
    assert [model["name"] for model in models] == ["model-a", "model-b"]
    assert captured["url"] == "http://localhost:11434/api/tags"


def test_byok_key_is_used_but_not_serialized(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured.update(url=url, headers=headers, json=json)
        return FakeResponse({
            "model": "remote", "choices": [{"message": {"content": "{\"answers\":[\"A\"]}"}}],
            "usage": {"total_tokens": 4}})

    monkeypatch.setattr("dove.model_clients.requests.post", fake_post)
    config = ModelConfig(
        name="remote", provider="openai_compatible",
        base_url="https://example.test/v1", model="model-1", api_key="secret-value")
    raw, metadata = chat(config, [{"role": "user", "content": "Question"}])
    assert raw == '{"answers":["A"]}'
    assert captured["headers"]["Authorization"] == "Bearer secret-value"
    assert "secret-value" not in str(config.model_dump())
    assert metadata["model"] == "remote"

