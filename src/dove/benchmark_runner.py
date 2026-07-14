from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from .answer_parser import parse_answer
from .model_clients import chat
from .schemas import BenchmarkItem, BenchmarkRun, ItemResult, ModelConfig
from .scorer import score_answer

ProgressCallback = Callable[[int, int, str, str], None]


def question_prompt(item: BenchmarkItem) -> str:
    options = "\n".join(f"{key}. {value}" for key, value in item.options.items())
    instruction = "Select exactly one option." if item.question_type == "single_choice" else "Select all correct options."
    return (
        "Answer this benchmark question without tools. "
        f"{instruction}\n{item.question}\n{options}\n"
        "Return only a JSON object with an answers array, for example: "
        "{\"answers\": [\"A\"]}"
    )


def run_benchmark(items: list[BenchmarkItem], models: list[ModelConfig],
                  benchmark_path: str = "",
                  progress: ProgressCallback | None = None) -> BenchmarkRun:
    started = datetime.now(timezone.utc).isoformat()
    results: list[ItemResult] = []
    total = len(items) * len(models)
    completed = 0
    for model in models:
        for item in items:
            if progress:
                progress(completed, total, model.name, item.id)
            try:
                raw, metadata = chat(model, [{"role": "user", "content": question_prompt(item)}])
                parsed = parse_answer(raw, list(item.options))
                score, exact = score_answer(item, parsed)
                results.append(ItemResult(
                    question_id=item.id, model_name=model.name, raw_response=raw,
                    parsed_answers=parsed, score=score, exact=exact,
                    model_metadata=metadata))
            except Exception as exc:
                results.append(ItemResult(
                    question_id=item.id, model_name=model.name, raw_response="",
                    parsed_answers=[], score=0, exact=False,
                    error=f"{type(exc).__name__}: {exc}"))
            completed += 1
            if progress:
                progress(completed, total, model.name, item.id)
    return BenchmarkRun(
        benchmark_path=benchmark_path, started_at=started,
        finished_at=datetime.now(timezone.utc).isoformat(),
        models=[m.model_dump(exclude={"api_key_env", "api_key"}) for m in models],
        questions=[q.model_dump() for q in items], results=results)


def save_run(run: BenchmarkRun, output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(run.model_dump(), indent=2), encoding="utf-8")

