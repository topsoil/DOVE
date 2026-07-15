import json
from pathlib import Path

from scripts.generate_html_report import export_report, render_report, summary_rows, subdomain_rows


def sample_run():
    return {
        "benchmark_path": "benchmark.json", "started_at": "start", "finished_at": "finish",
        "questions": [{"id": "q1", "subdomain": "RNA-seq", "question_type": "single_choice",
                       "question": "What input?", "options": {"A": "TPM", "B": "counts"},
                       "correct_answer": "B", "explanation": "Use integer counts."}],
        "results": [
            {"question_id": "q1", "model_name": "model-a", "parsed_answers": ["B"], "score": 1.0, "exact": True, "error": None},
            {"question_id": "q1", "model_name": "model-b", "parsed_answers": ["A"], "score": 0.0, "exact": False, "error": None},
        ],
    }


def test_report_aggregates_and_renders():
    run = sample_run()
    assert summary_rows(run)[0]["mean_score_percent"] == 100.0
    assert {row["subdomain"] for row in subdomain_rows(run)} == {"RNA-seq"}
    page = render_report(run, "Test report")
    assert "Test report" in page
    assert "Mean score by subdomain" in page
    assert "Subdomain evidence samples" in page
    assert "All question-level evidence" in page
    assert "Consistently correct — up to 5" in page
    assert "Inconsistent or incorrect — up to 5" in page
    assert "height:100.00%" in page


def test_report_exports_html_and_csv():
    folder = Path("data/results/headless-report-test")
    folder.mkdir(parents=True, exist_ok=True)
    source, report, summary = folder / "run.json", folder / "report.html", folder / "summary.csv"
    source.write_text(json.dumps(sample_run()), encoding="utf-8")
    export_report(source, report, "Test", summary)
    assert report.read_text(encoding="utf-8").startswith("<!doctype html>")
    assert "exact_accuracy_percent" in summary.read_text(encoding="utf-8")
    source.unlink(); report.unlink(); summary.unlink(); folder.rmdir()



