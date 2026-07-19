from __future__ import annotations

import argparse
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dove.interview import (InterviewResponse, InterviewResult, InterviewRun, interview_prompt,
                            load_interview_benchmark, load_sources, parse_interview_response,
                            save_interview_run, score_interview_response)
from dove.model_clients import chat
from dove.schemas import ModelConfig
from generate_interview_report import export_interview_report


def project_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def safe_filename(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("_")


def persist(run: InterviewRun, json_path: Path) -> None:
    tmp = json_path.with_name(json_path.name + ".tmp")
    save_interview_run(run, tmp)
    for attempt in range(40):
        try:
            tmp.replace(json_path)
            return
        except PermissionError:
            if attempt == 39:
                raise
            time.sleep(0.1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run DOVE interviews with per-answer checkpoints and resume")
    parser.add_argument("--config", required=True)
    parser.add_argument("--retry-errors", action="store_true")
    args = parser.parse_args()
    config = yaml.safe_load(Path(args.config).resolve().read_text(encoding="utf-8-sig")) or {}
    sources = load_sources(project_path(config["source_catalog"]))
    items = []
    for benchmark in config["benchmarks"]:
        rows = load_interview_benchmark(project_path(benchmark))
        limit = config.get("questions_per_benchmark")
        items.extend(rows[:int(limit)] if limit else rows)
    models = [ModelConfig.model_validate(model) for model in config["models"]]
    if not items or not models:
        parser.error("configuration must select at least one question and one model")
    output_dir = project_path(config.get("output_dir", "data/results/virtual_interview"))
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / config.get("run_filename", "virtual_interview_run.json")
    report_path = output_dir / config.get("report_filename", "virtual_interview_report.html")
    suite_name = config.get("suite_name", "DOVE virtual scientist interview")
    max_consecutive_errors = int(config.get("max_consecutive_errors", 3))
    max_model_errors = int(config.get("max_model_errors", 10))
    started_at = datetime.now(timezone.utc).isoformat()
    results = []
    completed = {}
    if json_path.exists():
        prior = InterviewRun.model_validate_json(json_path.read_text(encoding="utf-8-sig"))
        started_at = prior.started_at
        results = list(prior.results)
        completed = {(r.model_name, r.question_id): r for r in results
                     if not (args.retry_errors and r.error)}
        if args.retry_errors:
            results = [r for r in results if not r.error]
        print(f"RESUME {len(completed)} completed answer records from {json_path}", flush=True)
    total = len(items) * len(models)
    print(f"Interview questions: {len(items)} · Models: {len(models)} · Primary calls: {total}", flush=True)
    print("Checkpoint interval: every completed answer", flush=True)
    for model_no, model in enumerate(models, 1):
        print(f"MODEL START {model_no}/{len(models)}: {model.name}", flush=True)
        consecutive_errors = 0
        total_errors = sum(1 for r in results if r.model_name == model.name and r.error)
        for item_no, item in enumerate(items, 1):
            key = (model.name, item.id)
            overall_no = (model_no - 1) * len(items) + item_no
            if key in completed:
                print(f"[{overall_no:>4}/{total}] {model.name} · {item.id} · SKIP CHECKPOINT", flush=True)
                continue
            print(f"[{overall_no:>4}/{total}] {model.name} · {item.id}", flush=True)
            wall_start = time.perf_counter()
            try:
                raw, metadata = chat(model, [{"role": "user", "content": interview_prompt(item)}])
                response = parse_interview_response(raw)
                score, dimensions, criteria, flags = score_interview_response(item, response, None)
                metadata = dict(metadata or {})
                metadata["wall_seconds"] = round(time.perf_counter() - wall_start, 3)
                result = InterviewResult(
                    question_id=item.id, benchmark_id=item.benchmark_id, model_name=model.name,
                    raw_response=raw, response=response, score=score,
                    dimension_scores=dimensions, criteria=criteria,
                    triggered_red_flags=flags, model_metadata=metadata,
                )
                consecutive_errors = 0
            except Exception as exc:
                total_errors += 1
                consecutive_errors += 1
                result = InterviewResult(
                    question_id=item.id, benchmark_id=item.benchmark_id, model_name=model.name,
                    raw_response="", response=InterviewResponse(), score=0.0,
                    dimension_scores={}, criteria=[],
                    error=f"{type(exc).__name__}: {exc}",
                    model_metadata={"wall_seconds": round(time.perf_counter() - wall_start, 3)},
                )
                print(f"CALL ERROR {model.name} · {item.id}: {result.error}", flush=True)
            results.append(result)
            completed[key] = result
            cumulative = InterviewRun(
                suite_name=suite_name, started_at=started_at,
                finished_at=datetime.now(timezone.utc).isoformat(), sources=sources,
                models=[m.model_dump(exclude={"api_key_env", "api_key"}) for m in models],
                questions=items, results=results,
            )
            persist(cumulative, json_path)
            print(f"CHECKPOINT {len(results)}/{total} · {result.model_metadata.get('wall_seconds', 0):.1f}s", flush=True)
            if consecutive_errors >= max_consecutive_errors or total_errors >= max_model_errors:
                raise RuntimeError(
                    f"circuit breaker for {model.name}: {consecutive_errors} consecutive, {total_errors} total errors"
                )
        model_results = [r for r in results if r.model_name == model.name]
        partial = InterviewRun(
            suite_name=suite_name, started_at=started_at,
            finished_at=datetime.now(timezone.utc).isoformat(), sources=sources,
            models=[model.model_dump(exclude={"api_key_env", "api_key"})],
            questions=items, results=model_results,
        )
        model_report = output_dir / f"{report_path.stem}_{safe_filename(model.name)}_summary.html"
        model_answers = output_dir / f"{report_path.stem}_{safe_filename(model.name)}_answers.json"
        export_interview_report(partial.model_dump(), model_report)
        save_interview_run(partial, model_answers)
        print(f"MODEL COMPLETE {model_no}/{len(models)}: {model.name} · {len(model_results)} answers", flush=True)
        print(f"Model HTML report: {model_report}", flush=True)
        print(f"Model answer JSON: {model_answers}", flush=True)
    final = InterviewRun(
        suite_name=suite_name, started_at=started_at,
        finished_at=datetime.now(timezone.utc).isoformat(), sources=sources,
        models=[m.model_dump(exclude={"api_key_env", "api_key"}) for m in models],
        questions=items, results=results,
    )
    persist(final, json_path)
    export_interview_report(final.model_dump(), report_path)
    print(f"Run JSON: {json_path}", flush=True)
    print(f"Final across-model HTML report: {report_path}", flush=True)


if __name__ == "__main__":
    main()

