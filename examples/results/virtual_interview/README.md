# Large-model virtual-interview answer records

These files contain the complete per-question outputs used for the large-model extension of the DOVE biomedical and bioinformatics virtual scientist interview. They are committed so readers can audit the reported aggregate scores against the original model responses.

| Model | Questions | Recorded errors | Mean rubric score | Answer record | SHA-256 |
|---|---:|---:|---:|---|---|
| GPT-OSS 20B | 140 | 0 | 60.8% | [gpt-oss-20b_140_answers.json](gpt-oss-20b_140_answers.json) | `F5AC33275A821506BFF66C887E09B3BB06738C6D35BA3928B237DE35329BBB22` |
| Nemotron 3 33B | 140 | 0 | 50.2% | [nemotron3-33b_140_answers.json](nemotron3-33b_140_answers.json) | `004289E72F62FDD1110772CC1ECB55E7AABB9738B29821E458A70DD030BE2404` |

## Run configuration

Both runs used the local Ollama endpoint, temperature 0, an 8,192-token context window, a 700-token maximum output, and a 900-second request timeout. GPT-OSS used `thinking: low`; Nemotron used `thinking: false`. The model tags recorded by the runner were `gpt-oss:20b` and `nemotron3:33b`.

The JSON includes the 140 benchmark questions, raw and parsed responses, optional follow-up responses, rubric scores, dimension scores, red flags, timestamps, errors, and model metadata. No API keys or patient data are present.

## Interpretation boundary

The score is DOVE's deterministic rubric/phrase score, not a blinded expert judgment or proof of biomedical correctness. Use the answer-level records to inspect failures and borderline cases. Runtime checkpoint files and the combined seven-model JSON remain excluded from Git because they are redundant, much larger working artifacts; the two published files above are byte-identical to their runtime per-model checkpoints.

Verify the files in PowerShell:

~~~powershell
Get-FileHash .\examples\results\virtual_interview\gpt-oss-20b_140_answers.json -Algorithm SHA256
Get-FileHash .\examples\results\virtual_interview\nemotron3-33b_140_answers.json -Algorithm SHA256
~~~
