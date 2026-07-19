from __future__ import annotations

import json
from pathlib import Path

from dove.interview import (InterviewResponse, load_interview_benchmark,
                            score_interview_response)

ROOT = Path(__file__).resolve().parents[1]


def test_interview_suite_has_seven_twenty_question_benchmarks():
    index = json.loads((ROOT / "data/interview_benchmarks/suite_index.json").read_text(encoding="utf-8"))
    assert len(index) == 7
    assert sum(row["questions"] for row in index) == 140
    assert all(20 <= row["questions"] <= 30 for row in index)
    for row in index:
        items = load_interview_benchmark(ROOT / row["path"])
        assert len(items) == row["questions"]
        assert all(item.source_ids and item.reference_answer and item.rubric for item in items)
        assert all(item.review_status == "draft" for item in items)


def test_auditable_rubric_scoring_matches_and_flags():
    item = load_interview_benchmark(
        ROOT / "data/interview_benchmarks/L5_grounding_hallucination_20.json"
    )[0]
    good = InterviewResponse(
        answer="This is a false premise. A VUS means uncertain significance; do not fabricate a DOI and verify it."
    )
    score, dimensions, criteria, flags = score_interview_response(item, good)
    assert score == 1.0
    assert all(row["matched"] for row in criteria)
    assert dimensions
    assert not flags


def test_plain_text_response_is_supported():
    from dove.interview import parse_interview_response
    parsed = parse_interview_response("I would verify the source before answering.")
    assert parsed.answer.startswith("I would verify")


def test_model_config_accepts_ollama_reasoning_level():
    from dove.schemas import ModelConfig

    config = ModelConfig(
        name="gpt-oss",
        provider="ollama",
        model="gpt-oss:20b",
        base_url="http://localhost:11434",
        thinking="low",
    )
    assert config.thinking == "low"
