from __future__ import annotations

import json
import math
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from .corpus_ingest import ingest_corpus, save_corpus
from .llm_wiki import _context_batches, build_wiki, load_wiki_context_batches
from .question_generator import generate_questions_from_context, save_questions
from .schemas import BenchmarkItem, ModelConfig


def _id_prefix(domain: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", domain.lower()).strip("_") or "private_docs"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_experience_log(workspace: Path, log: dict) -> None:
    log["updated_at"] = _utc_now()
    (workspace / "experience_log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")


def _base_log(source: Path, output: str | Path, domain: str, count: int,
              model: ModelConfig, strategy: str) -> dict:
    return {
        "format": "dove_llm_experience_v2", "status": "running",
        "strategy": strategy, "started_at": _utc_now(),
        "documents_dir": str(source.resolve()), "output": str(Path(output).resolve()),
        "domain": domain, "requested_questions": count,
        "model": {"name": model.name, "provider": model.provider, "model": model.model,
                  "base_url": model.base_url, "temperature": model.temperature,
                  "timeout_seconds": model.timeout, "context_window": model.context_window,
                  "max_output_tokens": model.max_output_tokens,
                  "structured_outputs": model.structured_outputs},
        "stages": {}, "question_batches": [],
    }


def _validate_inputs(documents_dir: str | Path, count: int, batch_size: int,
                     max_rounds: int) -> Path:
    if count < 1:
        raise ValueError("count must be at least 1")
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    if max_rounds < 1:
        raise ValueError("max_rounds must be at least 1")
    source = Path(documents_dir)
    if not source.is_dir():
        raise ValueError(f"documents_dir is not a directory: {source}")
    return source


def _ingest(source: Path, work: Path, log: dict) -> dict:
    stage_started = time.perf_counter()
    corpus = ingest_corpus(source)
    log["stages"]["document_parsing"] = {
        "elapsed_seconds": round(time.perf_counter() - stage_started, 3),
        "documents": len(corpus["documents"]), "chunks": len(corpus["chunks"]),
        "characters": sum(len(chunk["text"]) for chunk in corpus["chunks"]),
    }
    save_experience_log(work, log)
    if not corpus["documents"]:
        raise ValueError("No supported documents found (expected PDF, Markdown, or text files)")
    if not corpus["chunks"]:
        raise ValueError("Documents were found, but no extractable text was produced")
    save_corpus(corpus, work / "corpus.json")
    return corpus


def _allocate_contexts(contexts: list[dict], count: int) -> list[dict]:
    if not contexts:
        raise ValueError("No source contexts are available for question generation")
    if count < len(contexts):
        indices = sorted({min(len(contexts) - 1, math.floor(i * len(contexts) / count))
                          for i in range(count)})
        selected = [contexts[index] for index in indices]
    else:
        selected = contexts
    base, extra = divmod(count, len(selected))
    return [{**context, "requested": base + (1 if index < extra else 0)}
            for index, context in enumerate(selected) if base + (1 if index < extra else 0) > 0]


def _generate_plan(model: ModelConfig, domain: str, subdomains: str, contexts: list[dict],
                   count: int, parallel: int, batch_size: int, max_rounds: int,
                   source_label: str, log: dict, work: Path) -> list[BenchmarkItem]:
    collected: list[BenchmarkItem] = []
    seen: set[str] = set()
    plan = _allocate_contexts(contexts, count)
    rounds = 0

    def run_task(task: dict) -> tuple[dict, list[BenchmarkItem], float, str | None]:
        started = time.perf_counter()
        try:
            result = generate_questions_from_context(
                model=model, domain=domain, n=task["requested"], context=task["context"],
                subdomains=subdomains, source_path=task.get("source_path"),
                source_pages=task.get("source_pages", []), source_label=source_label,
            )
            return task, result, round(time.perf_counter() - started, 3), None
        except Exception as exc:
            return task, [], round(time.perf_counter() - started, 3), f"{type(exc).__name__}: {exc}"

    while plan and len(collected) < count and rounds < max_rounds:
        rounds += 1
        results = []
        with ThreadPoolExecutor(max_workers=max(1, parallel)) as executor:
            futures = [executor.submit(run_task, task) for task in plan]
            for future in as_completed(futures):
                results.append(future.result())
        results.sort(key=lambda value: value[0]["index"])
        for task, candidates, elapsed, error in results:
            accepted = 0
            for item in candidates:
                key = " ".join(item.question.casefold().split())
                if key and key not in seen and len(collected) < count:
                    seen.add(key)
                    collected.append(item)
                    accepted += 1
            event = {
                "round": rounds, "context_index": task["index"],
                "source": task.get("source_path") or task.get("source_pages", []),
                "requested": task["requested"], "returned_valid": len(candidates),
                "accepted_unique": accepted, "cumulative_unique": len(collected),
                "elapsed_seconds": elapsed, "error": error,
            }
            log["question_batches"].append(event)
            print(
                f"[questions] round={rounds} context={task['index']} "
                f"accepted={accepted}/{task['requested']} total={len(collected)}/{count} "
                f"seconds={elapsed:.1f}" + (f" error={error}" if error else ""), flush=True,
            )
        save_experience_log(work, log)
        deficit = count - len(collected)
        if deficit <= 0:
            break
        retry_count = min(max(1, parallel), deficit)
        per_task = math.ceil(deficit / retry_count)
        plan = []
        for index in range(retry_count):
            context = contexts[((rounds * retry_count) + index) % len(contexts)]
            requested = min(batch_size, per_task, deficit - sum(t["requested"] for t in plan))
            if requested > 0:
                plan.append({**context, "requested": requested})

    log["stages"]["question_generation"] = {
        "elapsed_seconds": round(sum(x["elapsed_seconds"] for x in log["question_batches"]), 3),
        "rounds": rounds, "unique_questions": len(collected), "parallel": parallel,
        "source_contexts": len(contexts),
    }
    if len(collected) < count:
        raise RuntimeError(
            f"Model produced {len(collected)} unique valid questions after {rounds} rounds; "
            f"requested {count}. Increase --max-rounds or choose a stronger model."
        )
    return collected[:count]


def _normalize(items: list[BenchmarkItem], domain: str, source_label: str) -> list[BenchmarkItem]:
    prefix = _id_prefix(domain)
    normalized: list[BenchmarkItem] = []
    single_index = 0
    for index, item in enumerate(items, 1):
        updates = {"id": f"{prefix}_{index:04d}", "source": source_label,
                   "review_status": "corpus_generated"}
        if item.question_type == "single_choice" and item.correct_answer:
            desired = "ABCD"[single_index % 4]
            single_index += 1
            options = dict(item.options)
            current = item.correct_answer
            if current != desired and desired in options:
                options[current], options[desired] = options[desired], options[current]
            updates.update({"options": options, "correct_answer": desired})
        normalized.append(item.model_copy(update=updates))
    return normalized


def _finish(items: list[BenchmarkItem], output: str | Path, work: Path,
            log: dict, started: float) -> list[BenchmarkItem]:
    save_questions(items, output)
    log.update({"status": "success", "saved_questions": len(items),
                "finished_at": _utc_now(),
                "elapsed_seconds": round(time.perf_counter() - started, 3)})
    save_experience_log(work, log)
    return items


def generate_private_document_benchmark(
    documents_dir: str | Path, output: str | Path, workspace: str | Path,
    model: ModelConfig, domain: str, count: int, subdomains: str = "",
    batch_size: int = 20, max_rounds: int = 5, wiki_chunk_chars: int = 24000,
    question_context_chars: int = 40000, parallel: int = 1,
) -> list[BenchmarkItem]:
    """Full resumable LLM-Wiki strategy."""
    source = _validate_inputs(documents_dir, count, batch_size, max_rounds)
    work = Path(workspace); work.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter(); log = _base_log(source, output, domain, count, model, "wiki")
    save_experience_log(work, log)
    try:
        corpus = _ingest(source, work, log)
        stage_started = time.perf_counter()
        manifest = build_wiki(corpus, work, model, max_context_chars=wiki_chunk_chars)
        log["stages"]["wiki_compilation"] = {
            "elapsed_seconds": round(time.perf_counter() - stage_started, 3),
            "wiki_pages": len(manifest["pages"]),
            "cached_pages": sum(bool(page.get("cached")) for page in manifest["pages"]),
            "wiki_chunk_chars": wiki_chunk_chars,
        }
        save_experience_log(work, log)
        contexts = [
            {"index": index, "context": context, "source_pages": pages}
            for index, (context, pages) in enumerate(
                load_wiki_context_batches(work, question_context_chars)
            )
        ]
        items = _generate_plan(model, domain, subdomains, contexts, count, parallel,
                               batch_size, max_rounds, "karpathy_llm_wiki", log, work)
        return _finish(_normalize(items, domain, "karpathy_llm_wiki"), output, work, log, started)
    except Exception as exc:
        log.update({"status": "failed", "error": f"{type(exc).__name__}: {exc}",
                    "finished_at": _utc_now(),
                    "elapsed_seconds": round(time.perf_counter() - started, 3)})
        save_experience_log(work, log); raise


def generate_direct_document_benchmark(
    documents_dir: str | Path, output: str | Path, workspace: str | Path,
    model: ModelConfig, domain: str, count: int, subdomains: str = "",
    batch_size: int = 20, max_rounds: int = 5, source_chunk_chars: int = 40000,
    parallel: int = 4,
) -> list[BenchmarkItem]:
    """Fast direct strategy: extracted source segments to model, without wiki compilation."""
    source = _validate_inputs(documents_dir, count, batch_size, max_rounds)
    work = Path(workspace); work.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter(); log = _base_log(source, output, domain, count, model, "direct")
    save_experience_log(work, log)
    try:
        corpus = _ingest(source, work, log)
        contexts = []
        index = 0
        for document in corpus["documents"]:
            chunks = [c for c in corpus["chunks"] if c["document_id"] == document["id"]]
            for context, _ in _context_batches(chunks, source_chunk_chars):
                contexts.append({"index": index, "context": context,
                                 "source_path": document["path"], "source_pages": []})
                index += 1
        log["stages"]["direct_contexts"] = {
            "contexts": len(contexts), "source_chunk_chars": source_chunk_chars,
        }
        items = _generate_plan(model, domain, subdomains, contexts, count, parallel,
                               batch_size, max_rounds, "direct_private_documents", log, work)
        return _finish(_normalize(items, domain, "direct_private_documents"),
                       output, work, log, started)
    except Exception as exc:
        log.update({"status": "failed", "error": f"{type(exc).__name__}: {exc}",
                    "finished_at": _utc_now(),
                    "elapsed_seconds": round(time.perf_counter() - started, 3)})
        save_experience_log(work, log); raise
