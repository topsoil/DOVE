from pathlib import Path
from unittest.mock import mock_open, patch

from dove.corpus_ingest import ingest_corpus
from dove.llm_wiki import build_wiki
from dove.schemas import ModelConfig


def test_text_corpus_provenance():
    corpus = ingest_corpus("tests/fixtures")
    assert len(corpus["documents"]) == 1
    assert corpus["documents"][0]["sha256"]
    assert corpus["chunks"][0]["source_path"] == "private.md"


def test_wiki_write_contract_is_citable(monkeypatch):
    corpus = {
        "root": "private", "documents": [{"id": "abc", "path": "memo.md",
        "sha256": "deadbeef", "bytes": 10}],
        "chunks": [{"id": "abc_0001", "document_id": "abc", "source_path": "memo.md",
        "page": None, "text": "Internal fact"}]}
    monkeypatch.setattr("dove.llm_wiki.chat",
        lambda model, messages: ("Summary supported by [abc_0001].", {"model": "fake"}))
    model = ModelConfig(name="fake", provider="ollama", model="fake",
                        base_url="http://localhost")
    with patch.object(Path, "mkdir"), patch.object(Path, "write_text") as write_text,          patch.object(Path, "open", mock_open()):
        manifest = build_wiki(corpus, "vault", model)
    written_text = " ".join(str(call.args[0]) for call in write_text.call_args_list)
    assert "[abc_0001]" in written_text
    assert manifest["pages"][0]["source_sha256"] == "deadbeef"

def test_wiki_question_provenance_is_sanitized(monkeypatch):
    from dove.question_generator import generate_questions

    monkeypatch.setattr("dove.question_generator.load_wiki_context",
        lambda path: ("Fact [abc123def456_0001]", ["wiki/sources/memo.md"]))
    response = """[{"id":"q1","domain":"internal","subdomain":"policy",
      "question_type":"single_choice","question":"Which rule applies?",
      "options":{"A":"X","B":"Y","C":"Z","D":"W"},"correct_answer":"A",
      "correct_answers":null,"explanation":"From the memo.","difficulty":"basic",
      "tags":["private"],"provenance":{"source_pages":["invented.md"],
      "chunk_ids":["abc123def456_0001","fake_0001"]}}]"""
    monkeypatch.setattr("dove.question_generator.chat",
        lambda model, messages: (response, {}))
    model = ModelConfig(name="fake", provider="ollama", model="fake",
                        base_url="http://localhost")
    item = generate_questions(model, "internal", 1, wiki_dir="vault")[0]
    assert item.review_status == "corpus_generated"
    assert item.provenance["source_pages"] == ["wiki/sources/memo.md"]
    assert item.provenance["chunk_ids"] == ["abc123def456_0001"]
    assert item.provenance["citation_status"] == "verified_ids"

