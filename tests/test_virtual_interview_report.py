from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_interview_report import render_report


def test_interview_report_contains_candidate_matrix_and_sources():
    run = {
        "suite_name": "Test interview", "scoring_note": "Exploratory",
        "sources": [{"id": "S1", "title": "Source", "organization": "Org", "url": "https://example.org"}],
        "models": [{"name": "ollama:test"}],
        "questions": [{
            "id": "Q1", "benchmark_id": "L1", "category": "Foundations", "prompt": "Question?",
            "reference_answer": "Reference", "source_rationale": "Rationale", "source_ids": ["S1"],
        }],
        "results": [{
            "question_id": "Q1", "benchmark_id": "L1", "model_name": "ollama:test",
            "score": 2 / 3, "dimension_scores": {"scientific_reasoning": 2 / 3},
            "criteria": [{"description": "Missing concept", "matched": False}],
            "triggered_red_flags": [], "response": {"answer": "Answer", "uncertainty": "Some"},
        }],
    }
    report = render_report(run)
    assert "Candidate summary" in report
    assert "Capability matrix" in report
    assert "Lowest-scoring evidence" in report
    assert "Source" in report
