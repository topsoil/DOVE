# DOVE Tutorial

This tutorial walks through a small local comparison first, then shows how to
run the complete pilot benchmarks and add an OpenAI-compatible model.

## 1. Install DOVE

### Windows PowerShell

~~~powershell
cd <PATH-TO-DOVE>
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[app,pdf,dev]"
~~~

### macOS or Linux

~~~bash
cd <PATH-TO-DOVE>
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[app,pdf,dev]"
~~~

Confirm the installation:

~~~bash
python -m pytest -q
~~~

## 2. Prepare local Ollama models

Install Ollama separately, then check that its API is available:

~~~powershell
ollama list
~~~

Pull one or more models appropriate for your hardware. For example:

~~~powershell
ollama pull llama3.2:3b
ollama pull gemma3:1b
~~~

DOVE does not require these exact models. Any chat-capable models visible through
the local Ollama API can be selected.

## 3. Start DOVEboard

On Windows:

~~~powershell
.\run_doveboard.ps1
~~~

On macOS or Linux:

~~~bash
python -m streamlit run app/streamlit_app.py --server.port 8510
~~~

Open http://localhost:8510.

DOVE uses port 8510 by default so it can coexist with other Streamlit applications
that commonly use port 8501.

## 4. Choose a benchmark

Open the **Configure & run** tab.

Select one of:

- Bioinformatics best practices — 100 source-attributed drafts
- Disease genetics — 100 source-attributed drafts
- Small bioinformatics example — 2 questions
- Upload JSON/YAML

Expand **Preview benchmark**. The preview is paginated. Hover over a row to see:

- full question
- all answer choices
- gold answer
- explanation
- source

For a first test, select the two-question example.

## 5. Select local models

Under **Local Ollama**:

1. Confirm the URL is http://localhost:11434.
2. Click **Discover installed Ollama models**.
3. Select two, three, or four models.
4. If a model is not returned by discovery, enter its exact name under
   **Additional model names**.

DOVE assigns each model a stable chart color and displays grouped bars rather
than stacking model scores.

## 6. Run a small comparison

Set **Questions to run** to 2 or 5.

Click **Run benchmark**.

DOVE makes one call per question per model. For example:

| Questions | Models | Calls |
|---:|---:|---:|
| 5 | 2 | 10 |
| 100 | 4 | 400 |

Start small to confirm model availability and response parsing.

When the run finishes, download the full result JSON if you want a durable copy.

## 7. Interpret the results

Open **Results comparison**.

### Model comparison

The table reports:

- number of evaluated questions
- exact accuracy
- mean score
- call errors

### Mean score by subdomain

Models appear as separate colored bars. Every performance chart uses the same
0–100% y-axis, making model and subdomain comparisons consistent.

Hover over a bar to see the model, subdomain, and exact value.

### Question agreement explorer

The explorer is paginated to avoid a long page.

Status colors distinguish:

- Agree — all correct
- Agree — same incorrect answer
- Disagree

Hover over a question row to see:

- complete question
- gold answer
- separate answer and score for every selected model
- benchmark explanation

The full model-level table remains available in the collapsed raw-results
section.

## 8. Add a BYOK model

Under **OpenAI-compatible API**:

1. Enable **Add a remote/BYOK model**.
2. Enter a display name.
3. Enter the API base URL ending at the version root, such as
   https://api.example.com/v1.
4. Enter the provider's exact model ID.
5. Paste the API key into the password field.

The client sends requests to BASE_URL/chat/completions with Bearer
authentication. The key remains in the active Streamlit session and is excluded
from downloaded result JSON.

Always review the provider's privacy, retention, and cost policies before sending
benchmark content.

## 9. Run a complete pilot benchmark

After the small test succeeds:

1. Select a 100-question benchmark.
2. Select the desired models.
3. Set **Questions to run** to 100.
4. Confirm the total number of model calls.
5. Run and download the result JSON.

Four models across 100 questions require 400 sequential calls and may take a
while on local hardware.

## 10. Run from the command line

Copy the configuration example:

~~~powershell
Copy-Item config\models.example.yaml config\models.yaml
~~~

Edit config/models.yaml with local or OpenAI-compatible endpoints. Do not place
literal API keys in it; use api_key_env.

Run the pilot benchmark:

~~~powershell
python scripts\run_benchmark.py --benchmark data\benchmarks\bioinformatics_best_practices_100.json --models config\models.yaml --output data\results\bioinformatics_run.json --allow-unreviewed
~~~

Export a CSV summary:

~~~powershell
python scripts\export_report.py --results data\results\bioinformatics_run.json --output data\results\bioinformatics_summary.csv
~~~

## 11. Create a custom benchmark

A minimal single-choice item looks like this:

~~~json
[
  {
    "id": "example_001",
    "domain": "example",
    "subdomain": "fundamentals",
    "question_type": "single_choice",
    "question": "Which option is correct?",
    "options": {
      "A": "First choice",
      "B": "Second choice",
      "C": "Third choice",
      "D": "Fourth choice"
    },
    "correct_answer": "B",
    "correct_answers": null,
    "explanation": "The second choice is the intended answer.",
    "difficulty": "basic",
    "tags": ["example"],
    "source": "expert_curated",
    "review_status": "expert_reviewed",
    "version": "1.0"
  }
]
~~~

For multiple-select items, set question_type to multiple_select, set
correct_answer to null, and supply correct_answers such as ["A", "C"].

See [BENCHMARKS.md](BENCHMARKS.md) before distributing a benchmark as expert
reviewed.

## 12. Generate a benchmark from private documents

DOVE recursively extracts PDF and Markdown files and supports two strategies.
Keep private inputs outside Git or under `data\corpora`.

### Fast direct mode

Copy the model example and set the API key in the current shell:

~~~powershell
Copy-Item config\models.example.yaml config\models.yaml
$env:OPENAI_API_KEY = "YOUR_KEY"
~~~

Then send extracted source segments directly to the configured model. Calls run
in parallel, and supported endpoints can enforce a strict DOVE JSON schema:

~~~powershell
python scripts\generate_private_benchmark.py `
  --strategy direct `
  --documents "D:\private-documents" `
  --domain "Laboratory SOPs" `
  --subdomains "intake,processing,quality control,reporting" `
  --n 60 `
  --models config\models.yaml `
  --model openai_direct `
  --structured-outputs `
  --parallel 4 `
  --source-chunk-chars 40000 `
  --workspace data\corpora\laboratory_direct_work `
  --output data\generated_questions\laboratory_direct_60.json
~~~

This is fastest, but the endpoint receives extracted document text. Do not use
remote mode for confidential, unpublished, PHI, or regulated material without
appropriate institutional approval and data-retention controls.

### Full resumable LLM-Wiki mode

Confirm Ollama and the local model are available:

~~~powershell
ollama pull qwen3:4b
ollama list
~~~

Run in the foreground:

~~~powershell
python scripts\generate_private_benchmark.py `
  --strategy wiki `
  --documents "D:\private-documents" `
  --domain "Laboratory SOPs" `
  --n 60 `
  --ollama-model qwen3:4b `
  --ollama-context 8192 `
  --max-output-tokens 1800 `
  --wiki-chunk-chars 24000 `
  --question-context-chars 16000 `
  --batch-size 4 `
  --parallel 1 `
  --workspace data\corpora\laboratory_wiki `
  --output data\generated_questions\laboratory_wiki_60.json
~~~

Wiki pages are cached using the source content, model, prompt version, context
window, output limit, and chunk size. Re-running the identical command resumes
from completed compatible pages. Question generation is distributed across all
compiled wiki pages instead of only the first context window.

### Background execution

Use the supplied PowerShell launcher for long runs:

~~~powershell
.\scripts\run_private_benchmark_background.ps1 `
  -Strategy wiki `
  -Documents "D:\private-documents" `
  -Domain "Laboratory-SOPs" `
  -Questions 60 `
  -Output "data\generated_questions\laboratory_wiki_60.json" `
  -Workspace "data\corpora\laboratory_wiki" `
  -OllamaModel "qwen3:4b" `
  -OllamaContext 8192 `
  -MaxOutputTokens 1800 `
  -WikiChunkChars 24000 `
  -QuestionContextChars 16000 `
  -BatchSize 4 `
  -Parallel 1 `
  -JobName "laboratory-wiki"
~~~

Inspect progress without stopping it:

~~~powershell
.\scripts\status_private_benchmark.ps1 -JobName "laboratory-wiki" -Tail 40
~~~

The launcher records PID, stdout, and stderr under `data\results\background`.
The workspace contains `corpus.json`, persistent wiki pages,
`experience_log.json`, and per-page `wiki\experience.jsonl`. Completed output
can be uploaded to DOVEboard; `dimi_full_120.json` is also discovered
automatically when placed in `data\generated_questions`.

All generated items remain `corpus_generated`. Verify citations, answers,
explanations, distractors, sensitivity, and ambiguity before promotion. Scanned
image-only PDFs require OCR before local text extraction.
## Troubleshooting

### DOVEboard opens the wrong Streamlit app

Check the browser address. DOVEboard uses http://localhost:8510. Another app may
own port 8501.

### Ollama discovery fails

Confirm Ollama is running and that http://localhost:11434/api/tags is reachable.

### A model returns zero scores

Open the raw model-level rows and inspect raw_response and error. The model may
not have returned a parseable answer.

### Remote calls fail

Verify the base URL, model ID, API key, endpoint compatibility, and provider rate
limits.

## 13. Run a comparison and HTML report without the GUI

Create a working configuration:

~~~powershell
Copy-Item config\headless.example.yaml config\headless.yaml
notepad config\headless.yaml
~~~

Ensure every listed Ollama model is installed, then run:

~~~powershell
ollama list
python scripts\run_benchmark_report.py --config config\headless.yaml
~~~

No Streamlit process or browser click is involved. The default example writes:

~~~text
data/results/headless_bioinformatics/benchmark_run.json
data/results/headless_bioinformatics/benchmark_summary.csv
data/results/headless_bioinformatics/benchmark_report.html
~~~

Open the HTML file after the run if you want to inspect it. For an unattended
full run, set `question_limit: null` before starting. A failed model call is
recorded as an item-level error and does not abort the remaining comparison.

An existing result JSON can be rendered again without rerunning any model:

~~~powershell
python scripts\generate_html_report.py `
  --results data\results\headless_bioinformatics\benchmark_run.json `
  --output data\results\headless_bioinformatics\benchmark_report.html `
  --summary-csv data\results\headless_bioinformatics\benchmark_summary.csv `
  --title "DOVE bioinformatics comparison"
~~~

For complete benchmarks, the HTML report also creates one section per subdomain.
Each section contains its own fixed-scale model plot, up to five questions all
models answered correctly, and up to five model-disagreement, shared-incorrect,
or call-error cases. When a category has no examples, the report prints an
explicit empty-state message.

### Complete four-model disease-genetics example

A ready-to-run configuration compares Gemma 1B, Ministral 3B, TinyLlama 1.1B,
and MedGemma 4B across all 100 disease-genetics questions:

~~~powershell
python scripts\run_benchmark_report.py --config config\headless.genetics.example.yaml
~~~

This is one 400-call run and produces a single canonical JSON, CSV, and
`disease_genetics_100_report.html`. All four Ollama models must be installed.
