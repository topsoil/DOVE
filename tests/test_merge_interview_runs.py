from __future__ import annotations

import importlib.util
from pathlib import Path


def load_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "merge_interview_runs.py"
    spec = importlib.util.spec_from_file_location("merge_interview_runs", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_canonical_json_ignores_mapping_order():
    module = load_module()
    assert module.canonical_json({"b": 2, "a": 1}) == module.canonical_json({"a": 1, "b": 2})
