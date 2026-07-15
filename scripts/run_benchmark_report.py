from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dove.benchmark_loader import load_benchmark
from dove.benchmark_runner import run_benchmark, save_run
from dove.schemas import ModelConfig
from generate_html_report import export_report

REVIEWED = {"expert_reviewed", "consensus_reviewed"}


def project_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a configured DOVE benchmark and generate JSON, CSV, and HTML")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    benchmark_path = project_path(config["benchmark"])
    output_dir = project_path(config.get("output_dir", "data/results/headless"))
    output_dir.mkdir(parents=True, exist_ok=True)
    items = load_benchmark(benchmark_path)
    limit = config.get("question_limit")
    if limit is not None:
        if int(limit) < 1:
            parser.error("question_limit must be at least 1 or null")
        items = items[:int(limit)]
    models = [ModelConfig.model_validate(model) for model in config.get("models", [])]
    if not models:
        parser.error("configuration must contain at least one model")

    unreviewed = [item.id for item in items if item.review_status not in REVIEWED]
    if unreviewed and not config.get("allow_unreviewed", False):
        parser.error(f"refusing {len(unreviewed)} unreviewed questions; set allow_unreviewed: true for an exploratory run")

    def progress(completed: int, total: int, model: str, question: str) -> None:
        print(f"[{completed:>4}/{total}] {model} · {question}", flush=True)

    print(f"Benchmark: {benchmark_path}")
    print(f"Questions: {len(items)} · Models: {len(models)} · Calls: {len(items) * len(models)}")
    run = run_benchmark(items, models, str(benchmark_path), progress=progress)
    run_path = output_dir / config.get("run_filename", "benchmark_run.json")
    csv_path = output_dir / config.get("summary_filename", "benchmark_summary.csv")
    html_path = output_dir / config.get("report_filename", f"{benchmark_path.stem}_report.html")
    save_run(run, run_path)
    export_report(run_path, html_path, config.get("report_title", "DOVE benchmark report"), csv_path)
    print(f"Run JSON: {run_path}")
    print(f"Summary CSV: {csv_path}")
    print(f"HTML report: {html_path}")


if __name__ == "__main__":
    main()

