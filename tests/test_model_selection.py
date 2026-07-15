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



def test_ollama_runtime_limits_are_forwarded(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured.update(url=url, json=json, timeout=timeout)
        return FakeResponse({"message": {"content": "{}"}, "model": "qwen3:4b"})

    monkeypatch.setattr("dove.model_clients.requests.post", fake_post)
    config = ModelConfig(
        name="local", provider="ollama", base_url="http://localhost:11434",
        model="qwen3:4b", context_window=8192, max_output_tokens=1800, thinking=False,
    )
    chat(config, [{"role": "user", "content": "Test"}])
    assert captured["json"]["options"]["num_ctx"] == 8192
    assert captured["json"]["options"]["num_predict"] == 1800
    assert captured["json"]["think"] is False


def test_remote_structured_output_schema_is_forwarded(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured.update(json=json)
        return FakeResponse({"model": "remote", "choices": [{"message": {"content": "{}"}}]})

    monkeypatch.setattr("dove.model_clients.requests.post", fake_post)
    config = ModelConfig(
        name="remote", provider="openai_compatible", base_url="https://example.test/v1",
        model="model-1", structured_outputs=True,
    )
    schema = {"type": "json_schema", "json_schema": {"name": "test", "schema": {}}}
    chat(config, [{"role": "user", "content": "Test"}], response_format=schema)
    assert captured["json"]["response_format"] == schema
