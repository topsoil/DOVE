from __future__ import annotations

import os
import requests

from .schemas import ModelConfig


def list_ollama_models(base_url: str = "http://localhost:11434", timeout: int = 10) -> list[dict]:
    response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout)
    response.raise_for_status()
    return response.json().get("models", [])


def chat(config: ModelConfig, messages: list[dict[str, str]]) -> tuple[str, dict]:
    if config.provider == "ollama":
        response = requests.post(
            f"{config.base_url.rstrip('/')}/api/chat",
            json={"model": config.model, "messages": messages, "stream": False,
                  "format": "json", "options": {"temperature": config.temperature}},
            timeout=config.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"], {
            key: data.get(key) for key in
            ("model", "total_duration", "load_duration", "prompt_eval_count", "eval_count")
        }

    headers = {"Content-Type": "application/json"}
    key = config.api_key.get_secret_value() if config.api_key else None
    if not key and config.api_key_env:
        key = os.getenv(config.api_key_env)
        if not key:
            raise RuntimeError(f"Environment variable {config.api_key_env} is not set")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    response = requests.post(
        f"{config.base_url.rstrip('/')}/chat/completions", headers=headers,
        json={"model": config.model, "messages": messages,
              "temperature": config.temperature},
        timeout=config.timeout,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"], {
        "model": data.get("model"), "usage": data.get("usage")
    }



