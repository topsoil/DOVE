"""Rebuild DOVE's versioned seed benchmark JSON files."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "benchmark_sources"
OUT = ROOT / "data" / "benchmarks"


def records(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="|"))


def rotate(values: list[str], index: int):
    shift = index % 4
    ordered = values[shift:] + values[:shift]
    options = dict(zip("ABCD", ordered))
    return options, {value: label for label, value in options.items()}


def common(item_id: str, domain: str, row: dict, source_url: str, multiple=False):
    return {
        "id": item_id, "domain": domain, "subdomain": row["subdomain"],
        "question_type": "multiple_select" if multiple else "single_choice",
        "question": row["question"], "difficulty": "intermediate",
        "tags": [row["subdomain"].lower().replace(" ", "_"), "public_seed"],
        "source": source_url, "review_status": "llm_generated", "version": "1.0",
        "provenance": {
            "source_url": source_url,
            "curation_note": "AI-drafted public seed benchmark; expert review required before high-stakes use."
        }
    }


def build_bio() -> list[dict]:
    sources = json.loads((SOURCE / "bio_sources.json").read_text(encoding="utf-8"))
    output = []
    for index, row in enumerate(records(SOURCE / "bio_facts.psv"), 1):
        options, reverse = rotate(
            [row["answer"], row["d1"], row["d2"], row["d3"]], index)
        item = common(
            f"bio_bp_{index:03d}", "bioinformatics_best_practices",
            row, sources[row["source"]])
        item.update({
            "options": options, "correct_answer": reverse[row["answer"]],
            "correct_answers": None, "explanation": row["explanation"],
            "difficulty": ("basic", "intermediate", "advanced")[(index - 1) % 3],
        })
        output.append(item)
    for index, row in enumerate(records(SOURCE / "bio_multi.psv"), len(output) + 1):
        answers = row["answers"].split(";")
        options, reverse = rotate(answers + [row["distractor"]], index)
        item = common(
            f"bio_bp_{index:03d}", "bioinformatics_best_practices",
            row, sources[row["source"]], multiple=True)
        item.update({
            "options": options, "correct_answer": None,
            "correct_answers": sorted(reverse[answer] for answer in answers),
            "explanation": row["explanation"],
        })
        output.append(item)
    assert len(output) == 100, f"Expected 100 bioinformatics items, got {len(output)}"
    return output


def build_disease_genetics() -> list[dict]:
    rows = records(SOURCE / "disease_genetics.psv")
    gene_review = "https://www.ncbi.nlm.nih.gov/books/NBK1116/"
    inheritance_distractors = {
        "Autosomal dominant": ["Autosomal recessive", "X-linked", "Mitochondrial maternal"],
        "Autosomal recessive": ["Autosomal dominant", "X-linked", "Mitochondrial maternal"],
        "X-linked": ["Autosomal dominant", "Autosomal recessive", "Mitochondrial maternal"],
        "Mitochondrial maternal": ["Autosomal dominant", "Autosomal recessive", "X-linked"],
    }
    output = []
    genes = [row["gene"] for row in rows]
    for row_index, row in enumerate(rows):
        condition, gene, inheritance = row["condition"], row["gene"], row["inheritance"]
        gene_values = [gene, genes[(row_index + 7) % len(genes)],
                       genes[(row_index + 19) % len(genes)],
                       genes[(row_index + 31) % len(genes)]]
        gene_options, gene_reverse = rotate(gene_values, row_index * 2 + 1)
        gene_item = common(
            f"disease_gen_{row_index * 2 + 1:03d}", "disease_genetics",
            {"subdomain": row["subdomain"],
             "question": f"Which gene is most directly associated with {condition}?"},
            gene_review)
        gene_item.update({
            "options": gene_options, "correct_answer": gene_reverse[gene],
            "correct_answers": None,
            "explanation": f"{condition} is associated with disease-causing variation in {gene}.",
            "difficulty": "basic"})
        gene_item["provenance"]["source_locator"] = f"GeneReviews index: {condition}"
        output.append(gene_item)

        inheritance_values = [inheritance] + inheritance_distractors[inheritance]
        inheritance_options, inheritance_reverse = rotate(
            inheritance_values, row_index * 2 + 2)
        inheritance_item = common(
            f"disease_gen_{row_index * 2 + 2:03d}", "disease_genetics",
            {"subdomain": row["subdomain"],
             "question": f"What is the principal inheritance pattern of {condition}?"},
            gene_review)
        inheritance_item.update({
            "options": inheritance_options,
            "correct_answer": inheritance_reverse[inheritance],
            "correct_answers": None,
            "explanation": (f"{condition}, in the named gene context, is principally "
                            f"{inheritance.lower()}."),
            "difficulty": "intermediate"})
        inheritance_item["provenance"]["source_locator"] = f"GeneReviews index: {condition}"
        output.append(inheritance_item)
    assert len(output) == 100, f"Expected 100 disease-genetics items, got {len(output)}"
    return output


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bio = build_bio()
    (OUT / "bioinformatics_best_practices_100.json").write_text(
        json.dumps(bio, indent=2), encoding="utf-8")
    disease = build_disease_genetics()
    (OUT / "disease_genetics_100.json").write_text(
        json.dumps(disease, indent=2), encoding="utf-8")
    print(
        f"Wrote {len(bio)} bioinformatics and "
        f"{len(disease)} disease-genetics questions")


if __name__ == "__main__":
    main()


