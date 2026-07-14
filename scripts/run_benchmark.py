from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dove.benchmark_loader import load_benchmark, load_models
from dove.benchmark_runner import run_benchmark, save_run

REVIEWED = {"expert_reviewed", "consensus_reviewed"}


def main():
    parser = argparse.ArgumentParser(description="Run a DOVE benchmark")
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--models", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--allow-unreviewed", action="store_true",
        help="Explicitly allow draft/generated candidates (unsafe for reported scores)")
    args = parser.parse_args()
    items, models = load_benchmark(args.benchmark), load_models(args.models)
    unreviewed = [item.id for item in items if item.review_status not in REVIEWED]
    if unreviewed and not args.allow_unreviewed:
        parser.error("refusing unreviewed questions: " + ", ".join(unreviewed)
            + "; curate them or pass --allow-unreviewed for exploratory runs")
    run = run_benchmark(items, models, args.benchmark)
    save_run(run, args.output)
    print(f"Saved {len(run.results)} results to {args.output}")


if __name__ == "__main__":
    main()

