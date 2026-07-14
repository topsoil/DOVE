from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

TEXT_SUFFIXES = {".txt", ".md", ".rst", ".csv", ".json", ".yaml", ".yml"}


def _extract(path: Path) -> list[tuple[int | None, str]]:
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("Install the PDF extra: pip install 'dove-eval[pdf]'") from exc
        return [(number, page.extract_text() or "") for number, page in enumerate(PdfReader(path).pages, 1)]
    if path.suffix.lower() in TEXT_SUFFIXES:
        return [(None, path.read_text(encoding="utf-8", errors="replace"))]
    return []


def _chunks(text: str, size: int = 4000, overlap: int = 400) -> Iterable[str]:
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            boundary = text.rfind("\n", start, end)
            end = boundary if boundary > start + size // 2 else end
        value = text[start:end].strip()
        if value:
            yield value
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)


def ingest_corpus(input_path: str | Path) -> dict:
    root = Path(input_path)
    paths = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
    documents, chunks = [], []
    for path in paths:
        extracted = _extract(path)
        if not extracted:
            continue
        rel = str(path.relative_to(root)) if root.is_dir() else path.name
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        doc_id = digest[:12]
        documents.append({"id": doc_id, "path": rel, "sha256": digest, "bytes": path.stat().st_size})
        index = 0
        for page, text in extracted:
            for value in _chunks(text):
                index += 1
                chunks.append({"id": f"{doc_id}_{index:04d}", "document_id": doc_id,
                    "source_path": rel, "page": page, "text": value})
    return {"format": "dove_corpus_v1", "root": str(root.resolve()), "documents": documents, "chunks": chunks}


def save_corpus(corpus: dict, output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(corpus, indent=2), encoding="utf-8")

