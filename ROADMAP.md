# Roadmap

This roadmap separates near-term usability work from experimental research
features. Priorities may change based on user feedback.

## Before the first public release

- Select and add an explicit software and benchmark-data license.
- Complete human expert review of both 100-question pilot benchmarks.
- Add reviewer identity, decision, notes, and review date to benchmark provenance.
- Add screenshots or a short DOVEboard demonstration.
- Confirm package and project names do not conflict with existing public projects.
- Run CI on Windows, macOS, and Linux.
- Add a code of conduct and contribution guidelines if accepting contributions.

## Near term

### Benchmark execution

- Concurrent model calls with configurable safe limits.
- Cancellation, retry, exponential backoff, and resumable runs.
- Repeated runs for stochasticity.
- Prompt-template comparison.
- Estimated token usage, latency, and provider cost.
- Optional run budgets and hard spending limits.
- Pinned model and prompt versions.

### DOVEboard

- Multiple simultaneous BYOK endpoints.
- Saved local run history with explicit user-controlled storage.
- Side-by-side latency and token-usage charts.
- Question search and reviewer notes.
- Click-to-pin question details in addition to hover.
- Exportable HTML and PDF comparison reports.
- Accessibility and keyboard-navigation review.

### Benchmark governance

- Consensus review workflow.
- Inter-rater agreement.
- Benchmark release manifests and checksums.
- Temporal benchmark mode.
- Question retirement and replacement workflow.
- Benchmark contamination and memorization checks.
- Difficulty calibration from empirical model performance.

## Medium term

- RAG versus non-RAG comparison.
- Error-injection benchmarks.
- Confidence calibration.
- Free-text answer evaluation.
- Pairwise model significance testing and uncertainty intervals.
- Stratified and reproducible question sampling.
- Support for additional provider APIs.
- Batch API integration for large evaluations.

## Experimental private-document track

The current corpus ingestion and question-generation code is a scaffold.

Future work may include:

- Persistent Karpathy-style LLM-Wiki compilation.
- Incremental source updates and contradiction tracking.
- Full-text and vector retrieval.
- Source-page and chunk-level citation validation.
- Prompt-injection defenses for untrusted documents.
- PII and PHI detection/redaction hooks.
- Encryption, access control, retention, and audit policy.
- Human approval before generated questions enter a benchmark.
- Wiki versus raw-RAG ablation studies.

## Long term

- Plugin architecture for scorers, parsers, providers, and report formats.
- Distributed benchmark execution.
- Organization-level benchmark registries.
- Signed benchmark releases.
- Reproducible public leaderboards with submission validation.

