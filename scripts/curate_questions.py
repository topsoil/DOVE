from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import json
from pathlib import Path
from dove.schemas import BenchmarkItem


def main():
    parser = argparse.ArgumentParser(description="Promote selected candidates after human review")
    parser.add_argument("--input", required=True)
    parser.add_argument("--approve", required=True, help="Comma-separated question IDs")
    parser.add_argument("--status", choices=["expert_reviewed", "consensus_reviewed"], default="expert_reviewed")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    approved = {value.strip() for value in args.approve.split(",") if value.strip()}
    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    output = []
    for value in raw:
        if value.get("id") in approved:
            value["review_status"] = args.status
            output.append(BenchmarkItem.model_validate(value).model_dump())
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Promoted {len(output)} human-reviewed questions")


if __name__ == "__main__":
    main()


