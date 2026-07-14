from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .model_clients import chat
from .schemas import ModelConfig


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:80] or "source"


def build_wiki(corpus: dict, output_dir: str | Path, model: ModelConfig) -> dict:
    """Compile immutable raw-source chunks into persistent, citable Markdown pages.

    This follows Karpathy's LLM Wiki pattern: sources remain authoritative and
    untouched; generated wiki pages form a durable, improving synthesis layer.
    """
    output = Path(output_dir)
    wiki = output / "wiki"
    sources = wiki / "sources"
    concepts = wiki / "concepts"
    sources.mkdir(parents=True, exist_ok=True)
    concepts.mkdir(parents=True, exist_ok=True)

    pages = []
    for document in corpus["documents"]:
        chunks = [c for c in corpus["chunks"] if c["document_id"] == document["id"]]
        context = "\n\n".join(
            f"[{c['id']}] (page {c.get('page') or 'n/a'})\n{c['text']}" for c in chunks
        )
        prompt = f"""Compile this private source into one durable wiki page.
Use only the supplied source. Add inline citations like [chunk_id].
Include: Summary, Key facts, Concepts, Caveats, and Candidate benchmark themes.
Never expose knowledge not present in the source.

SOURCE: {document['path']}
{context[:60000]}"""
        text, metadata = chat(model, [{"role": "user", "content": prompt}])
        name = f"{_slug(document['path'])}-{document['id']}.md"
        header = (
            "---\n"
            f"source_path: {json.dumps(document['path'])}\n"
            f"source_sha256: {document['sha256']}\n"
            f"compiled_at: {datetime.now(timezone.utc).isoformat()}\n"
            f"model: {json.dumps(model.model)}\n"
            "---\n\n"
        )
        (sources / name).write_text(header + text.strip() + "\n", encoding="utf-8")
        pages.append({"path": f"wiki/sources/{name}", "source_path": document["path"],
                      "source_sha256": document["sha256"], "model_metadata": metadata})

    links = "\n".join(f"- [[sources/{Path(p['path']).name}|{p['source_path']}]]" for p in pages)
    (wiki / "overview.md").write_text(
        "# Private knowledge wiki\n\n"
        "Persistent compiled knowledge for source-grounded benchmark authoring.\n\n"
        "## Source pages\n\n" + links + "\n", encoding="utf-8")
    log = wiki / "log.md"
    with log.open("a", encoding="utf-8") as handle:
        handle.write(f"- {datetime.now(timezone.utc).isoformat()}: compiled {len(pages)} source pages\n")
    manifest = {"format": "dove_llm_wiki_v1", "pages": pages, "corpus_root": corpus.get("root")}
    (output / ".dove_wiki_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def load_wiki_context(wiki_dir: str | Path, max_chars: int = 60000) -> tuple[str, list[str]]:
    root = Path(wiki_dir)
    files = sorted((root / "wiki").rglob("*.md"))
    parts, citations, used = [], [], 0
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        remaining = max_chars - used
        if remaining <= 0:
            break
        rel = str(path.relative_to(root))
        parts.append(f"### WIKI PAGE: {rel}\n{text[:remaining]}")
        citations.append(rel)
        used += min(len(text), remaining)
    return "\n\n".join(parts), citations

