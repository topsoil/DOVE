from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dove.report_generator import export_summary


def main():
    parser = argparse.ArgumentParser(description="Export a DOVE result summary")
    parser.add_argument("--results", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    export_summary(args.results, args.output)
    print(f"Saved summary to {args.output}")


if __name__ == "__main__":
    main()


