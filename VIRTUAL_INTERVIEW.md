# DOVE virtual scientist interview

DOVE's open-ended interview suite evaluates whether a local model can function as a supervised biomedical/bioinformatics collaborator—not merely answer trivia. Seven progressive benchmarks contain 20 source-grounded scenarios each (140 total): foundations, best-practice reasoning, real-world problem solving, evidence interpretation, hallucination resistance, senior-scientist collaboration, and adversarial reliability.

Each item contains a reference answer, auditable criterion-level rubric, capability dimensions, red flags, authoritative source IDs, provenance rationale, and an optional adversarial follow-up. The authoritative URL catalog is `data/interview_sources/authoritative_sources.json`.

The baseline configuration uses locally installed Ollama tags for Llama 3.2, TinyLlama, Qwen 2.5 3B, Ministral 3 3B, and GLM 4.7 Flash. The large-model extension adds GPT-OSS 20B and Nemotron 3 33B. The completed seven-model example contains 980 responses.

## Generate and run

From the repository root:

```powershell
python scripts/emit_virtual_interview_benchmarks.py
python scripts/run_virtual_interview.py --config config/virtual_interview.local.yaml
```

For a quick one-model, seven-question check:

```powershell
python scripts/run_virtual_interview.py --config config/virtual_interview.smoke.yaml
```

The five-model baseline makes 700 primary calls; the two-model extension makes 280. Long runs should use `run_virtual_interview_incremental.py`, which checkpoints every answer and resumes by model/question key. Start with the smoke configuration before a full run.

## Reading the report

The standalone HTML report compares interview levels and capability dimensions, identifies low-scoring answers, exposes each reference answer and missing criterion, and recommends a provisional operating boundary.

Scores are deterministic phrase/rubric coverage indicators, not proof of scientific correctness. This makes every point auditable and avoids a hidden LLM judge, but it can miss valid synonyms and nuanced reasoning. All interview items remain `draft` until qualified domain experts approve prompts, expected answers, synonyms, source versions, and operating-boundary thresholds. Exploratory configurations must therefore set `allow_unreviewed: true` explicitly.

## Large-model extension and completed example

The tested configuration uses an 8,192-token context and a 700-token generation ceiling. GPT-OSS uses `thinking: low`; Nemotron uses thinking disabled. Reasoning behavior is model-specific, so do not change these settings without a smoke test that confirms a valid final JSON answer.

```powershell
python scripts/run_virtual_interview_incremental.py --config config/virtual_interview.large_local.yaml
```

After the baseline and extension complete, merge them with `scripts/merge_interview_runs.py`. The public example reports are:

- `examples/reports/biomedical_bioinformatics_virtual_interview_7models_report.html`
- `examples/reports/DOVE_7Model_Biomedical_Bioinformatics_Technical_Report.docx`
- `examples/results/virtual_interview/gpt-oss-20b_140_answers.json`
- `examples/results/virtual_interview/nemotron3-33b_140_answers.json`

The raw 980-response JSON is intentionally excluded from Git. It should be retained locally with appropriate access, redaction, and release controls.
