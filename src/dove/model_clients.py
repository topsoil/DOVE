from __future__ import annotations

import os
from typing import Any

import requests

from .schemas import ModelConfig


def list_ollama_models(base_url: str = "http://localhost:11434", timeout: int = 10) -> list[dict]:
    response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout)
    response.raise_for_status()
    return response.json().get("models", [])


def chat(
    config: ModelConfig,
    messages: list[dict[str, str]],
    response_format: dict[str, Any] | None = None,
) -> tuple[str, dict]:
    if config.provider == "ollama":
        options: dict[str, Any] = {"temperature": config.temperature}
        if config.context_window:
            options["num_ctx"] = config.context_window
        if config.max_output_tokens:
            options["num_predict"] = config.max_output_tokens
        request_body: dict[str, Any] = {"model": config.model, "messages": messages, "stream": False,
                                        "format": "json", "options": options}
        if config.thinking is not None:
            request_body["think"] = config.thinking
        response = requests.post(
            f"{config.base_url.rstrip('/')}/api/chat",
            json=request_body,
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
    payload: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature,
    }
    if config.max_output_tokens:
        payload["max_completion_tokens"] = config.max_output_tokens
    if response_format and config.structured_outputs:
        payload["response_format"] = response_format
    response = requests.post(
        f"{config.base_url.rstrip('/')}/chat/completions", headers=headers,
        json=payload, timeout=config.timeout,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"], {
        "model": data.get("model"), "usage": data.get("usage")
    }
