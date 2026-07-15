from pathlib import Path
from unittest.mock import patch

from dove.private_document_benchmark import generate_private_document_benchmark
from dove.schemas import BenchmarkItem, ModelConfig


def _candidate(question: str) -> BenchmarkItem:
    return BenchmarkItem(
        id="temporary",
        domain="internal",
        subdomain="policy",
        question_type="single_choice",
        question=question,
        options={"A": "Alpha", "B": "Beta", "C": "Gamma", "D": "Delta"},
        correct_answer="A",
        explanation="Supported by the private source.",
        source="karpathy_llm_wiki",
        review_status="corpus_generated",
        provenance={"source_pages": ["wiki/sources/private.md"]},
    )


def _model() -> ModelConfig:
    return ModelConfig(
        name="fake", provider="ollama", model="fake", base_url="http://localhost"
    )


def test_private_pipeline_enforces_count_and_dove_contract(monkeypatch):
    corpus = {
        "documents": [{"id": "abc", "path": "private.md"}],
        "chunks": [{"id": "abc_0001", "text": "Private fact"}],
    }
    calls = {"value": 0}
    saved = {}
    logs = []

    monkeypatch.setattr("dove.private_document_benchmark.ingest_corpus", lambda path: corpus)
    monkeypatch.setattr("dove.private_document_benchmark.save_corpus", lambda data, path: None)
    monkeypatch.setattr(
        "dove.private_document_benchmark.save_experience_log",
        lambda work, log: logs.append(dict(log)),
    )
    monkeypatch.setattr(
        "dove.private_document_benchmark.build_wiki",
        lambda data, work, model: {"pages": [{"path": "wiki/sources/private.md"}]},
    )

    def fake_generate(**kwargs):
        calls["value"] += 1
        return [_candidate(f"Question {calls['value']}-{i}?") for i in range(kwargs["n"])]

    monkeypatch.setattr("dove.private_document_benchmark.generate_questions", fake_generate)
    monkeypatch.setattr(
        "dove.private_document_benchmark.save_questions",
        lambda items, output: saved.update(items=items, output=output),
    )

    with patch.object(Path, "is_dir", return_value=True), patch.object(Path, "mkdir"):
        items = generate_private_document_benchmark(
            documents_dir="private-documents",
            output="benchmark.json",
            workspace="wiki-workspace",
            model=_model(),
            domain="Internal Policy",
            count=3,
            batch_size=2,
        )

    assert len(items) == 3
    assert [item.id for item in items] == [
        "internal_policy_0001",
        "internal_policy_0002",
        "internal_policy_0003",
    ]
    assert all(item.review_status == "corpus_generated" for item in items)
    assert all(item.source == "karpathy_llm_wiki" for item in items)
    assert saved["items"] == items
    assert logs[-1]["status"] == "success"
    assert logs[-1]["stages"]["document_parsing"]["documents"] == 1


def test_private_pipeline_rejects_empty_directory(monkeypatch):
    monkeypatch.setattr(
        "dove.private_document_benchmark.save_experience_log", lambda work, log: None
    )
    monkeypatch.setattr(
        "dove.private_document_benchmark.ingest_corpus",
        lambda path: {"documents": [], "chunks": []},
    )
    with patch.object(Path, "is_dir", return_value=True), patch.object(Path, "mkdir"):
        try:
            generate_private_document_benchmark(
                documents_dir="empty-documents",
                output="out.json",
                workspace="workspace",
                model=_model(),
                domain="Internal",
                count=1,
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
