from pathlib import Path
from unittest.mock import patch

from dove.private_document_benchmark import (
    generate_direct_document_benchmark,
    generate_private_document_benchmark,
)
from dove.schemas import BenchmarkItem, ModelConfig


def _candidate(question: str) -> BenchmarkItem:
    return BenchmarkItem(
        id="temporary", domain="internal", subdomain="policy",
        question_type="single_choice", question=question,
        options={"A": "Alpha", "B": "Beta", "C": "Gamma", "D": "Delta"},
        correct_answer="A", explanation="Supported by the private source.",
        source="karpathy_llm_wiki", review_status="corpus_generated",
        provenance={"source_pages": ["wiki/sources/private.md"],
                    "chunk_ids": ["abc123def456_0001"]},
    )


def _model() -> ModelConfig:
    return ModelConfig(name="fake", provider="ollama", model="fake",
                       base_url="http://localhost")


def _corpus():
    return {
        "documents": [{"id": "abc123def456", "path": "private.md",
                       "sha256": "deadbeef", "bytes": 10}],
        "chunks": [{"id": "abc123def456_0001", "document_id": "abc123def456",
                    "source_path": "private.md", "page": None, "text": "Private fact"}],
    }


def _common_mocks(monkeypatch, logs, saved):
    monkeypatch.setattr("dove.private_document_benchmark.ingest_corpus", lambda path: _corpus())
    monkeypatch.setattr("dove.private_document_benchmark.save_corpus", lambda data, path: None)
    monkeypatch.setattr("dove.private_document_benchmark.save_experience_log",
                        lambda work, log: logs.append(dict(log)))
    monkeypatch.setattr("dove.private_document_benchmark.save_questions",
                        lambda items, output: saved.update(items=items, output=output))


def test_wiki_pipeline_enforces_count_and_dove_contract(monkeypatch):
    saved, logs, calls = {}, [], {"value": 0}
    _common_mocks(monkeypatch, logs, saved)
    monkeypatch.setattr(
        "dove.private_document_benchmark.build_wiki",
        lambda data, work, model, max_context_chars: {
            "pages": [{"path": "wiki/sources/private.md", "cached": False}]},
    )
    monkeypatch.setattr(
        "dove.private_document_benchmark.load_wiki_context_batches",
        lambda work, limit: [("Fact [abc123def456_0001]", ["wiki/sources/private.md"])],
    )

    def fake_generate(**kwargs):
        calls["value"] += 1
        return [_candidate(f"Question {calls['value']}-{i}?") for i in range(kwargs["n"])]

    monkeypatch.setattr("dove.private_document_benchmark.generate_questions_from_context", fake_generate)
    with patch.object(Path, "is_dir", return_value=True), patch.object(Path, "mkdir"):
        items = generate_private_document_benchmark(
            "private-documents", "benchmark.json", "wiki-workspace", _model(),
            "Internal Policy", 3, batch_size=2,
        )
    assert [item.id for item in items] == [
        "internal_policy_0001", "internal_policy_0002", "internal_policy_0003"
    ]
    assert all(item.review_status == "corpus_generated" for item in items)
    assert saved["items"] == items
    assert logs[-1]["status"] == "success"


def test_direct_pipeline_uses_source_context_without_wiki(monkeypatch):
    saved, logs = {}, []
    _common_mocks(monkeypatch, logs, saved)
    monkeypatch.setattr(
        "dove.private_document_benchmark.generate_questions_from_context",
        lambda **kwargs: [_candidate(f"Direct {i}?") for i in range(kwargs["n"])],
    )
    with patch.object(Path, "is_dir", return_value=True), patch.object(Path, "mkdir"):
        items = generate_direct_document_benchmark(
            "private-documents", "direct.json", "direct-work", _model(),
            "Internal", 4, parallel=2,
        )
    assert len(items) == 4
    assert all(item.source == "direct_private_documents" for item in items)
    assert logs[-1]["strategy"] == "direct"


def test_private_pipeline_rejects_empty_directory(monkeypatch):
    monkeypatch.setattr("dove.private_document_benchmark.save_experience_log", lambda work, log: None)
    monkeypatch.setattr("dove.private_document_benchmark.ingest_corpus",
                        lambda path: {"documents": [], "chunks": []})
    with patch.object(Path, "is_dir", return_value=True), patch.object(Path, "mkdir"):
        try:
            generate_private_document_benchmark(
                "empty-documents", "out.json", "workspace", _model(), "Internal", 1
            )
        except ValueError as exc:
            assert "No supported documents" in str(exc)
        else:
            raise AssertionError("Expected empty document directory to be rejected")


def test_long_wiki_sources_are_split_without_losing_chunks():
    from dove.llm_wiki import _context_batches
    chunks = [
        {"id": "abc_0001", "page": 1, "text": "A" * 30000},
        {"id": "abc_0002", "page": 2, "text": "B" * 30000},
    ]
    batches = _context_batches(chunks, max_chars=50000)
    assert len(batches) == 2
    assert [chunk_id for _, ids in batches for chunk_id in ids] == ["abc_0001", "abc_0002"]


def test_wiki_cache_signature_changes_with_runtime_limits():
    from dove.llm_wiki import _signature
    first = _model().model_copy(update={"context_window": 8192, "max_output_tokens": 900})
    second = first.model_copy(update={"max_output_tokens": 1200})
    assert _signature(first, "same context", 24000) == _signature(first, "same context", 24000)
    assert _signature(first, "same context", 24000) != _signature(second, "same context", 24000)
