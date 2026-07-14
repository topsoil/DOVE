from __future__ import annotations

import json
from pathlib import Path

import yaml

from .schemas import BenchmarkItem, ModelConfig


def _read(path: str | Path):
    path = Path(path)
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) if path.suffix.lower() in {".yaml", ".yml"} else json.load(handle)


def load_benchmark(path: str | Path) -> list[BenchmarkItem]:
    data = _read(path)
    if isinstance(data, dict):
        data = data.get("questions", data.get("items"))
    if not isinstance(data, list):
        raise ValueError("Benchmark must be a list or contain a 'questions' list")
    return [BenchmarkItem.model_validate(item) for item in data]


def load_models(path: str | Path) -> list[ModelConfig]:
    data = _read(path)
    models = data.get("models") if isinstance(data, dict) else data
    if not isinstance(models, list):
        raise ValueError("Model config must contain a 'models' list")
    return [ModelConfig.model_validate(model) for model in models]

