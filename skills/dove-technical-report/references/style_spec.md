# DOVE report style specification

Use this specification when a DOVE technical report should match the established Claude-Code reference report while remaining original and data-driven.

## Page architecture

- US Letter portrait with compact margins near 0.6–0.7 inch.
- Arial body text around 9.5–10.5 pt with 1.05–1.15 line spacing.
- Small running header: `LOCAL LLM BIOMEDICAL EVALUATION` at left and `DOVE TECHNICAL REPORT` at right.
- Footer separated by a thin rule: research-only safety label at left, report date at center, and page number at right.
- Prefer `Page X` to a fragile total-page field unless the final total is materialized after rendering.

## Color system

- Navy `#0B2545`: titles, table headers, major structure.
- Teal `#007681`: rules, section navigation, secondary emphasis.
- Purple `#68478D`: qualitative-example headings.
- Blue `#3D6FB4`: neutral quantitative accents.
- Green `#2E7D32` with pale fill: supported or positive behavior.
- Amber `#C77700` with pale fill: caution and qualified utility.
- Red `#B3261E` with pale fill: safety failures and no-go findings.
- Pale gray/blue: alternating table rows and metadata panels.

## Cover

Use a navy kicker band, a large navy title, a teal italic subtitle, a short report label/date block, a four-cell metric strip, one evidence-based headline finding, one red scope/safety notice, and repository attribution. The headline must be regenerated from the current run.

## Body hierarchy

- Heading 1: navy, bold, with a teal bottom rule.
- Heading 2: teal, bold.
- Evidence/example label: purple, bold.
- Tables: navy header with white text, compact cells, alternating pale rows.
- Callouts: titled boxes with semantic fill, never color alone; always include text labels.

## Charts

Use a fixed 0–100 y-axis for comparable scores. Preserve one color per model across every chart. Keep legends close, labels horizontal when possible, and include numeric values when the plot remains readable. Heatmaps should include cell values and a clearly labeled percent scale.

## Voice

Write as a technical evaluator speaking to biomedical informatics trainees, scientists, and clinical governance readers. Lead readers through why each failure matters in an actual analysis or clinical workflow. Avoid marketing language, empty slogans, and claims that model size alone establishes safety.
