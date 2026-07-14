from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


def summary_rows(run: dict) -> list[dict]:
    groups = defaultdict(list)
    for result in run["results"]:
        groups[result["model_name"]].append(result)
    return [{"model": model, "questions": len(rows),
        "exact_accuracy": sum(bool(r["exact"]) for r in rows) / len(rows),
        "mean_score": sum(float(r["score"]) for r in rows) / len(rows),
        "errors": sum(bool(r.get("error")) for r in rows)}
        for model, rows in sorted(groups.items())]


def export_summary(result_path: str | Path, output: str | Path) -> None:
    run = json.loads(Path(result_path).read_text(encoding="utf-8"))
    rows = summary_rows(run)
    with Path(output).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["model"])
        writer.writeheader()
        writer.writerows(rows)

