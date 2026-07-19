from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge compatible DOVE interview runs without duplicating models")
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--suite-name")
    args = parser.parse_args()
    runs = [load(p.resolve()) for p in args.inputs]
    reference = runs[0]
    question_fingerprint = canonical_json(reference["questions"])
    source_fingerprint = canonical_json(reference["sources"])
    for path, run in zip(args.inputs[1:], runs[1:]):
        if canonical_json(run["questions"]) != question_fingerprint:
            raise SystemExit(f"question catalog differs: {path}")
        if canonical_json(run["sources"]) != source_fingerprint:
            raise SystemExit(f"source catalog differs: {path}")
    models = []
    results = []
    names = set()
    result_keys = set()
    for run in runs:
        for model in run["models"]:
            name = model["name"]
            if name in names:
                raise SystemExit(f"duplicate model: {name}")
            names.add(name)
            models.append(model)
        for result in run["results"]:
            key = (result["model_name"], result["question_id"])
            if key in result_keys:
                raise SystemExit(f"duplicate result: {key}")
            result_keys.add(key)
            results.append(result)
    expected = len(reference["questions"])
    counts = {name: sum(r["model_name"] == name for r in results) for name in names}
    incomplete = {name: count for name, count in counts.items() if count != expected}
    if incomplete:
        raise SystemExit(f"incomplete model records: expected {expected}, found {incomplete}")
    errors = [r for r in results if r.get("error")]
    merged = {
        "suite_name": args.suite_name or reference["suite_name"],
        "started_at": min(r["started_at"] for r in runs),
        "finished_at": max(r["finished_at"] for r in runs),
        "sources": reference["sources"],
        "models": models,
        "questions": reference["questions"],
        "results": results,
        "scoring_note": reference.get("scoring_note", ""),
        "merge_metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "inputs": [str(p.resolve()) for p in args.inputs],
            "models": len(models),
            "questions_per_model": expected,
            "responses": len(results),
            "errors": len(errors),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merged["merge_metadata"], indent=2))
    print(args.output.resolve())


if __name__ == "__main__":
    main()
