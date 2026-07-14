# 🕊️ DOVE

**DOVE — Domain-Oriented AI/LLMs Validation & Evaluation** is a lightweight
Python framework for running and comparing domain-specific multiple-choice LLM
benchmarks.

Its Streamlit interface, **DOVEboard**, can compare multiple local Ollama models
and an optional bring-your-own-key OpenAI-compatible endpoint in the same run.

## Highlights

- Discover and select multiple locally installed Ollama models.
- Add an OpenAI-compatible model with an in-session API key.
- Load benchmark questions from JSON or YAML.
- Score single-choice and multiple-select questions.
- Apply exact scoring and partial credit for multiple-select answers.
- Compare models with grouped, color-coded bars on fixed 0–100% axes.
- Explore agreement and disagreement using paginated hover details.
- Export complete results as JSON and summaries as CSV.
- Preserve raw responses, parsed answers, timestamps, errors, and model metadata.
- Keep API keys out of result files and version-controlled configuration.

## Included pilot benchmarks

| Benchmark | Questions | Coverage |
|---|---:|---|
| Bioinformatics best practices | 100 | Sequencing QC, formats, RNA-seq, variants, cancer genomics, single-cell, metagenomics, reproducibility, study design |
| Disease genetics | 100 | Gene–disease associations and principal inheritance patterns for 50 disorders |
| Small bioinformatics example | 2 | Minimal single- and multiple-select demonstration |

The two 100-question sets are AI-drafted, source-attributed pilot benchmarks.
They are marked llm_generated, not expert gold. They are appropriate for
software demonstrations and exploratory model comparisons. Domain experts
should review them before scientific reporting, clinical use, or publication.

See [BENCHMARKS.md](BENCHMARKS.md) for schema, provenance, and review guidance.

## Quick start

Requirements:

- Python 3.10 or newer
- Optional: [Ollama](https://ollama.com/) for local models

### Windows PowerShell

~~~powershell
git clone <YOUR-REPOSITORY-URL>
cd dove

python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[app,dev]"

.\run_doveboard.ps1
~~~

Open http://localhost:8510.

### macOS or Linux

~~~bash
git clone <YOUR-REPOSITORY-URL>
cd dove

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[app,dev]"

python -m streamlit run app/streamlit_app.py --server.port 8510
~~~

For a guided first comparison, see [TUTORIAL.md](TUTORIAL.md).

## Run tests

~~~bash
python -m pytest -q
~~~

## Command-line example

Copy and edit the model configuration:

~~~powershell
Copy-Item config\models.example.yaml config\models.yaml
~~~

Then run:

~~~powershell
python scripts\run_benchmark.py --benchmark data\benchmarks\bioinformatics_best_practices_100.json --models config\models.yaml --output data\results\bioinformatics_run.json --allow-unreviewed
~~~

The explicit --allow-unreviewed flag is required for the included pilot
benchmarks. Curated benchmarks marked expert_reviewed or consensus_reviewed do
not require it.

## Project structure

~~~text
app/                         DOVEboard Streamlit application
config/                      Model configuration example
data/
  benchmark_sources/         Reviewable source fact banks
  benchmarks/                Included JSON benchmarks
  corpora/                   Local private documents; ignored by Git
  generated_questions/       Generated drafts; ignored by Git
  results/                   Run outputs; ignored by Git
prompts/                     Question-generation prompt contracts
scripts/                     CLI tools and benchmark builder
src/dove/                    Python package
tests/                       Automated tests
TUTORIAL.md                  End-to-end walkthrough
BENCHMARKS.md                Schema and benchmark review notes
ROADMAP.md                   Planned work
~~~

## Privacy and credentials

DOVEboard holds a manually entered API key only in the active Streamlit session.
The key is excluded from result JSON and model metadata. Never commit
config/models.yaml, .env files, private corpora, or generated result files
containing sensitive prompts or responses.

Local Ollama requests stay on the configured Ollama endpoint. Remote models
receive benchmark question text through the configured API endpoint.

## Experimental private-document work

Corpus ingestion and private-document question-generation scaffolding is
included for experimentation, but the persistent LLM-Wiki workflow is deferred
to a later phase. Treat generated questions as drafts requiring human review.

## License

A project license has not yet been selected. Choose and add a license before
treating this repository as an open-source release.


