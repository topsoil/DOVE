---
name: dove-technical-report
description: Build or update evidence-grounded DOVE technical reports from completed benchmark run JSON and question/source catalogs. Use for multi-model biomedical or bioinformatics evaluations that need reproducible metrics, qualitative positive and negative examples, safety interpretation, a polished DOCX, or a report styled to match the DOVE navy/teal reference design.
---

# DOVE Technical Report

Create a full evaluation report only from completed, inspectable artifacts. Treat the report as a traceable analysis product, not promotional copy.

## Required inputs

Locate and inspect:

- the completed DOVE run JSON, including every model's raw responses, parsed responses, scores, criteria, red flags, errors, and timestamps;
- the benchmark question files and authoritative source catalog used by that run;
- any reference PDF or DOCX supplied for visual style or section structure;
- the DOVE scorer implementation when interpreting automated scores.

If a requested model is incomplete, preserve its checkpointed answers but do not present it as complete. State the exact completed-question count and exclude missing records from unqualified across-model comparisons.

## Workflow

1. Validate the run before writing.
   - Confirm unique model names, question count per model, total responses, and error counts.
   - Verify that question IDs and benchmark IDs join to the question catalog.
   - Record model tags, provider, parameters, run timestamps, output-token counts, and available latency metadata.
2. Recompute every reported metric from the final JSON.
   - Overall mean score by model.
   - Mean score by interview level and scoring dimension.
   - Score distribution and count of triggered red flags.
   - Runtime and completion statistics where the metadata supports them.
   - Never copy old totals or rankings from a previous report.
3. Audit the scorer.
   - Inspect substantive answers that receive zero or low phrase-coverage scores.
   - Inspect high-scoring answers for unsafe claims that happen to match expected phrases.
   - Describe deterministic coverage as rubric coverage, not clinical accuracy.
4. Select qualitative evidence.
   - Include both positive and negative examples for every interview level.
   - Prioritize shared failures, model disagreement, false-premise resistance, identifiability errors, invented tools or citations, unsupported precision, and actionable safety failures.
   - Attribute observations to exact question IDs and models; paraphrase long model responses.
5. Write the report in this order: cover, abstract, executive summary, report map, abbreviations, introduction/motivation, methods, overview results, level-by-level results, cross-cutting discussion, deployment guidance, limitations, future work, references, detailed appendix, deployment checklist.
6. Generate charts with a common 0–100 scale where scores are compared. Use consistent model colors and legible labels. Include an overall bar chart, interview-level heatmap, dimension heatmap, and at least one operational or distribution view when supported.
7. Create and verify the DOCX using the documents workflow. Render to page images when LibreOffice is available and inspect every page. If rendering is unavailable, perform structural checks and say explicitly that visual rendering was not completed.

## Interpretation rules

- Separate privacy from epistemic safety: local hosting changes the data-control boundary but does not ensure correct reasoning.
- Separate relative ranking from absolute validity.
- Treat a single prompt/run as an estimate, not model identity.
- Identify non-identifiable designs explicitly; do not imply that statistical adjustment can repair perfect confounding.
- Do not convert benchmark output into patient-specific clinical advice.
- Distinguish answer-model generation from judge-model scoring whenever a model judge is used; report exact immutable model snapshots and blinding procedures.
- Keep external or planned evaluation arms out of Results until their answer and judge records exist.

## Visual system

Read [style specification](references/style_spec.md) before formatting. Use compact, editorial pages with navy structure, teal navigation accents, purple example headings, and reserved amber/red/green assessment callouts. Avoid slogan-only pages, oversized whitespace, decorative gradients, and dashboard-like clutter.

## Completion checklist

Before delivery, confirm:

- all requested models are represented with truthful completion status;
- reported counts equal the run JSON;
- rankings and narrative claims agree with recomputed tables;
- each level contains traceable positive and negative evidence;
- limitations cover scorer mismatch, one-run instability, benchmark review status, model/version drift, and clinical non-validation;
- the DOCX opens as a valid ZIP package and has no clipped tables or obviously stale page totals;
- repository paths in the appendix point to the actual final artifacts.
