from __future__ import annotations

import json
import re
from pathlib import Path

from .llm_wiki import load_wiki_context
from .model_clients import chat
from .schemas import BenchmarkItem, ModelConfig


def _json_payload(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(?:\x60{3}|~~~)(?:json)?\s*(.*?)(?:\x60{3}|~~~)", text, re.S | re.I)
        if match:
            return json.loads(match.group(1))
        start, end = text.find("["), text.rfind("]")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise


def _prompt(domain: str, n: int, context: str = "", subdomains: str = "") -> str:
    grounding = (
        "Every claim must be supported by the WIKI CONTEXT. Include provenance.source_pages "
        "and provenance.chunk_ids. Avoid questions answerable from general public knowledge."
        if context else "Use established domain knowledge and mark provenance as domain_prompt."
    )
    return f"""Generate {n} candidate benchmark questions for {domain}.
Subdomains: {subdomains or 'mixed'}
{grounding}
Return only a JSON array matching DOVE fields: id, domain, subdomain, question_type
(single_choice or multiple_select), question, options (A-D), correct_answer,
correct_answers, explanation, difficulty, tags, source, review_status, version,
provenance. Distractors must be plausible. Do not use 'all of the above'.
Generated items are candidates for human review, never final gold data.

WIKI CONTEXT:
{context}"""


def generate_questions(model: ModelConfig, domain: str, n: int, subdomains: str = "",
                       wiki_dir: str | Path | None = None) -> list[BenchmarkItem]:
    context, pages = load_wiki_context(wiki_dir) if wiki_dir else ("", [])
    raw, _ = chat(model, [{"role": "user", "content": _prompt(domain, n, context, subdomains)}])
    data = _json_payload(raw)
    if isinstance(data, dict):
        data = data.get("questions", [])
    items = []
    for index, value in enumerate(data, 1):
        value["id"] = value.get("id") or f"{_safe(domain)}_{index:04d}"
        value["source"] = "karpathy_llm_wiki" if wiki_dir else "llm_domain_prompt"
        value["review_status"] = "corpus_generated" if wiki_dir else "llm_generated"
        value["version"] = str(value.get("version", "0.1"))
        provenance = value.setdefault("provenance", {})
        if wiki_dir:
            reported_pages = provenance.get("source_pages") or []
            provenance["source_pages"] = [p for p in reported_pages if p in pages] or pages
            valid_chunks = set(re.findall(r"\[([0-9a-f]{12}_\d{4})\]", context))
            reported_chunks = provenance.get("chunk_ids") or []
            provenance["chunk_ids"] = [c for c in reported_chunks if c in valid_chunks]
            provenance["citation_status"] = (
                "verified_ids" if provenance["chunk_ids"] else "human_verification_required"
            )
            provenance["wiki_dir"] = str(Path(wiki_dir).resolve())
        items.append(BenchmarkItem.model_validate(value))
    return items


def _safe(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def save_questions(items: list[BenchmarkItem], output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([item.model_dump() for item in items], indent=2), encoding="utf-8")



