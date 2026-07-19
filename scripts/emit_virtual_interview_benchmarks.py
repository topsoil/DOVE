from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interview_benchmarks"


def load_levels(path: Path) -> dict:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module.LEVELS


def split_terms(value: str) -> list[str]:
    return [part.strip() for part in value.split("|")]


def main() -> None:
    levels = {}
    for filename in ("build_virtual_interview_benchmarks.py", "interview_specs_advanced.py", "interview_specs_senior.py"):
        levels.update(load_levels(Path(__file__).with_name(filename)))
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for level, data in sorted(levels.items()):
        items = []
        for number, (prompt, reference, sources, concepts) in enumerate(data["items"], 1):
            rubric = []
            for position, concept in enumerate(concepts):
                rubric.append({
                    "id": f"C{position+1}",
                    "dimension": data["dimensions"][position % len(data["dimensions"])],
                    "description": f"Addresses: {concept.replace('|', ' / ')}",
                    "match_any": split_terms(concept),
                    "weight": 1.0,
                })
            item_id = f"VI_L{level}_{number:02d}"
            items.append({
                "id": item_id, "benchmark_id": data["id"], "level": level,
                "category": data["category"], "domain": "biomedical_bioinformatics",
                "prompt": prompt, "reference_answer": reference, "rubric": rubric,
                "source_ids": sources,
                "source_rationale": "The expected reasoning is bounded by the listed authoritative standards, official documentation, regulatory material, or primary guideline.",
                "follow_up_prompt": "Are you sure? Identify the most dangerous unsupported assumption in your answer and revise it." if level >= 5 else None,
                "red_flags": [{
                    "description": "Claims certainty or universal validity without qualification",
                    "match_any": ["guaranteed", "always correct", "zero risk", "proves all"],
                    "penalty": 0.2,
                }],
                "difficulty": ["basic", "intermediate", "skilled", "advanced", "expert", "senior", "adversarial"][level-1],
                "review_status": "draft", "tags": [f"level_{level}", "virtual_interview", "source_grounded"],
            })
        if len(items) < 20 or len(items) > 30:
            raise RuntimeError(f"{data['id']} has {len(items)} items; expected 20-30")
        output = OUT / f"{data['id']}_20.json"
        output.write_text(json.dumps({"benchmark": data["id"], "items": items}, indent=2), encoding="utf-8")
        index.append({"level": level, "benchmark": data["id"], "questions": len(items), "path": str(output.relative_to(ROOT)).replace("\\", "/")})
    (OUT / "suite_index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"Wrote {sum(x['questions'] for x in index)} questions across {len(index)} benchmarks to {OUT}")


if __name__ == "__main__":
    main()
