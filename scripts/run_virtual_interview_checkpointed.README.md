# Resilient virtual interview runner

Run `python scripts/run_virtual_interview_checkpointed.py --config config/virtual_interview.local.yaml` to execute models sequentially.

After each model, the runner writes a model-only HTML report, a model-only answer JSON, the cumulative run JSON, and the cumulative across-model HTML report. The default circuit breaker skips the remaining calls for a model after three consecutive or ten total call errors, records skipped questions with the reason, checkpoints the failed-model report, and continues with the next configured model.
