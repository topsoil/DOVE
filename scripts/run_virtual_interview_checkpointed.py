from __future__ import annotations

import argparse
import re
import sys
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


def run_one_model(items, model, sources, suite_name, run_followups, max_consecutive_errors,
                  max_model_errors, global_offset, global_total):
    started = datetime.now(timezone.utc).isoformat()
    results = []
    consecutive_errors = 0
    total_errors = 0
    breaker_reason = None
    for index, item in enumerate(items):
        overall = global_offset + index
        print(f"[{overall:>4}/{global_total}] {model.name} · {item.id}", flush=True)
        try:
            raw, metadata = chat(model, [{"role": "user", "content": interview_prompt(item)}])
            response = parse_interview_response(raw)
            follow_raw = ""
            follow_response = None
            if run_followups and item.follow_up_prompt:
                follow_raw, follow_meta = chat(model, [
                    {"role": "user", "content": interview_prompt(item)},
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": f"Follow-up: {item.follow_up_prompt}\nReturn the same JSON structure."},
                ])
                follow_response = parse_interview_response(follow_raw)
                metadata["follow_up"] = follow_meta
            score, dimensions, criteria, flags = score_interview_response(item, response, follow_response)
            results.append(InterviewResult(
                question_id=item.id, benchmark_id=item.benchmark_id, model_name=model.name,
                raw_response=raw, response=response, follow_up_raw_response=follow_raw,
                follow_up_response=follow_response, score=score, dimension_scores=dimensions,
                criteria=criteria, triggered_red_flags=flags, model_metadata=metadata,
            ))
            consecutive_errors = 0
        except Exception as exc:
            total_errors += 1
            consecutive_errors += 1
            message = f"{type(exc).__name__}: {exc}"
            results.append(InterviewResult(
                question_id=item.id, benchmark_id=item.benchmark_id, model_name=model.name,
                raw_response="", response=InterviewResponse(), score=0.0, dimension_scores={},
                criteria=[], error=message,
            ))
            print(f"CALL ERROR {model.name} · {item.id}: {message}", flush=True)
        if consecutive_errors >= max_consecutive_errors or total_errors >= max_model_errors:
            breaker_reason = (f"circuit breaker after {consecutive_errors} consecutive and "
                              f"{total_errors} total call errors")
            print(f"MODEL CIRCUIT BREAKER: {model.name} · {breaker_reason}", flush=True)
            for remaining in items[index + 1:]:
                results.append(InterviewResult(
                    question_id=remaining.id, benchmark_id=remaining.benchmark_id,
                    model_name=model.name, raw_response="", response=InterviewResponse(),
                    score=0.0, dimension_scores={}, criteria=[],
                    error=f"Skipped: {breaker_reason}",
                ))
            break
    print(f"[{global_offset + len(items):>4}/{global_total}] {model.name} · COMPLETE", flush=True)
    return InterviewRun(
        suite_name=suite_name, started_at=started,
        finished_at=datetime.now(timezone.utc).isoformat(), sources=sources,
        models=[model.model_dump(exclude={"api_key_env", "api_key"})],
        questions=items, results=results,
    ), breaker_reason


def main() -> None:
    parser = argparse.ArgumentParser(description="Run DOVE interviews with resilient per-model checkpoints")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = yaml.safe_load(Path(args.config).resolve().read_text(encoding="utf-8")) or {}
    sources = load_sources(project_path(config["source_catalog"]))
    items = []
    for benchmark in config["benchmarks"]:
        rows = load_interview_benchmark(project_path(benchmark))
        limit = config.get("questions_per_benchmark")
        items.extend(rows[:int(limit)] if limit else rows)
    models = [ModelConfig.model_validate(model) for model in config["models"]]
    if not items or not models:
        parser.error("configuration must select at least one question and one model")
    unreviewed = [x.id for x in items if x.review_status not in {"expert_reviewed", "consensus_reviewed"}]
    if unreviewed and not config.get("allow_unreviewed", False):
        parser.error(f"refusing {len(unreviewed)} non-expert-reviewed items; set allow_unreviewed: true")

    output_dir = project_path(config.get("output_dir", "data/results/virtual_interview"))
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / config.get("run_filename", "virtual_interview_run.json")
    report_path = output_dir / config.get("report_filename", "virtual_interview_report.html")
    suite_name = config.get("suite_name", "DOVE virtual scientist interview")
    max_consecutive_errors = int(config.get("max_consecutive_errors", 3))
    max_model_errors = int(config.get("max_model_errors", 10))
    suite_started = datetime.now(timezone.utc).isoformat()
    all_results = []
    completed_models = []
    total_calls = len(items) * len(models)

    print(f"Interview questions: {len(items)} · Models: {len(models)} · Primary calls: {total_calls}", flush=True)
    print(f"Circuit breaker: {max_consecutive_errors} consecutive or {max_model_errors} total errors/model", flush=True)
    for model_number, model in enumerate(models, 1):
        print(f"MODEL START {model_number}/{len(models)}: {model.name}", flush=True)
        partial, breaker_reason = run_one_model(
            items, model, sources, suite_name, bool(config.get("run_followups", False)),
            max_consecutive_errors, max_model_errors, (model_number - 1) * len(items), total_calls,
        )
        all_results.extend(partial.results)
        completed_models.append(model)
        cumulative = InterviewRun(
            suite_name=suite_name, started_at=suite_started,
            finished_at=datetime.now(timezone.utc).isoformat(), sources=sources,
            models=[m.model_dump(exclude={"api_key_env", "api_key"}) for m in completed_models],
            questions=items, results=all_results,
        )
        save_interview_run(cumulative, json_path)
        export_interview_report(cumulative.model_dump(), report_path)
        model_report = output_dir / f"{report_path.stem}_{safe_filename(model.name)}_summary.html"
        export_interview_report(partial.model_dump(), model_report)
        model_answers = output_dir / f"{report_path.stem}_{safe_filename(model.name)}_answers.json"
        save_interview_run(partial, model_answers)
        status = f"FAILED/SKIPPED — {breaker_reason}" if breaker_reason else "COMPLETED"
        print(f"MODEL COMPLETE {model_number}/{len(models)}: {model.name} · {status}", flush=True)
        print(f"Model HTML report: {model_report}", flush=True)
        print(f"Model answer JSON: {model_answers}", flush=True)
        print(f"Cumulative HTML report: {report_path}", flush=True)

    print(f"Run JSON: {json_path}", flush=True)
    print(f"Final across-model HTML report: {report_path}", flush=True)


if __name__ == "__main__":
    main()


