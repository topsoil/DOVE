from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dove.interview import (load_interview_benchmark, load_sources, run_interview,
                            save_interview_run)
from dove.schemas import ModelConfig
from generate_interview_report import export_interview_report


def project_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the DOVE virtual-scientist interview suite")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = yaml.safe_load(Path(args.config).resolve().read_text(encoding="utf-8")) or {}
    sources = load_sources(project_path(config["source_catalog"]))
    items = []
    for benchmark in config["benchmarks"]:
        benchmark_items = load_interview_benchmark(project_path(benchmark))
        limit = config.get("questions_per_benchmark")
        items.extend(benchmark_items[:int(limit)] if limit else benchmark_items)
    models = [ModelConfig.model_validate(model) for model in config["models"]]
    if not items or not models:
        parser.error("configuration must select at least one question and one model")
    unreviewed = [item.id for item in items if item.review_status not in {"expert_reviewed", "consensus_reviewed"}]
    if unreviewed and not config.get("allow_unreviewed", False):
        parser.error(
            f"refusing {len(unreviewed)} non-expert-reviewed interview items; "
            "set allow_unreviewed: true for an exploratory run"
        )
    output_dir = project_path(config.get("output_dir", "data/results/virtual_interview"))
    output_dir.mkdir(parents=True, exist_ok=True)

    def progress(done: int, total: int, model: str, question: str) -> None:
        print(f"[{done:>4}/{total}] {model} · {question}", flush=True)

    print(f"Interview questions: {len(items)} · Models: {len(models)} · Primary calls: {len(items) * len(models)}")
    run = run_interview(
        items, models, sources, config.get("suite_name", "DOVE virtual scientist interview"),
        run_followups=bool(config.get("run_followups", False)), progress=progress,
    )
    json_path = output_dir / config.get("run_filename", "virtual_interview_run.json")
    report_path = output_dir / config.get("report_filename", "virtual_interview_report.html")
    save_interview_run(run, json_path)
    export_interview_report(run.model_dump(), report_path)
    print(f"Run JSON: {json_path}")
    print(f"HTML report: {report_path}")


if __name__ == "__main__":
    main()
