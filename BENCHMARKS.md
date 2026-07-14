# Benchmarks

DOVE benchmarks are JSON or YAML lists of multiple-choice items.

## Included files

### data/benchmarks/bioinformatics_best_practices_100.json

- 100 questions
- 90 single-choice
- 10 multiple-select
- 10 subdomains
- source-attributed pilot content

### data/benchmarks/disease_genetics_100.json

- 100 single-choice questions
- 50 named disorders
- gene–disease and principal inheritance questions
- 12 subdomains
- source-attributed pilot content

### data/benchmarks/bioinformatics_v0_1.json

A two-question example for quick software testing.

## Review status

The two 100-question sets are marked llm_generated. That status is intentional.
They have automated schema checks and source attribution, but have not undergone
documented human domain-expert review.

Do not present them as clinically validated, publication-ready, or expert gold
without reviewing every item.

Recommended review checks:

1. Verify the answer against the linked current source.
2. Confirm that the question has one defensible answer set.
3. Check whether disease names, inheritance statements, or guidelines have
   changed.
4. Review distractors for plausibility and unintended ambiguity.
5. Confirm that the explanation justifies the answer without adding unsupported
   claims.
6. Record reviewer identity, date, decision, and notes.
7. Promote accepted items to expert_reviewed or consensus_reviewed.
8. Increment the benchmark version and preserve a change record.

## Item schema

~~~json
{
  "id": "bioinfo_001",
  "domain": "bioinformatics",
  "subdomain": "RNA-seq QC",
  "question_type": "single_choice",
  "question": "What should be checked before differential-expression analysis?",
  "options": {
    "A": "Run differential expression immediately",
    "B": "Inspect QC and batch structure",
    "C": "Remove all genes with low p-values",
    "D": "Normalize only case samples"
  },
  "correct_answer": "B",
  "correct_answers": null,
  "explanation": "QC and batch structure should be inspected first.",
  "difficulty": "basic",
  "tags": ["RNA-seq", "QC"],
  "source": "https://example.org/source",
  "review_status": "expert_reviewed",
  "version": "1.0",
  "provenance": {
    "source_url": "https://example.org/source"
  }
}
~~~

For multiple-select items:

- question_type is multiple_select
- correct_answer is null
- correct_answers contains one or more option labels

Supported review statuses:

- draft
- llm_generated
- corpus_generated
- expert_reviewed
- consensus_reviewed
- retired

## Scoring

Single-choice answers receive 1 for an exact match and 0 otherwise.

Multiple-select answers receive 1 for an exact set match. Partial credit is:

~~~text
max(0, (true selections - false selections) / number of gold selections)
~~~

## Rebuilding the pilot files

The compact source banks are stored in data/benchmark_sources.

Rebuild the JSON files with:

~~~bash
python scripts/build_seed_benchmarks.py
~~~

Tests verify question counts, IDs, schema validity, uniqueness, and balanced
single-choice answer positions.

## Versioning guidance

A released benchmark should have:

- an immutable version identifier
- a review record
- source access dates
- a documented scoring policy
- a retirement process for outdated or ambiguous questions
- contamination and memorization considerations

