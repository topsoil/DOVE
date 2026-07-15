from __future__ import annotations

import argparse
import csv
import html
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def summary_rows(run: dict) -> list[dict]:
    groups = defaultdict(list)
    for result in run.get("results", []):
        groups[result["model_name"]].append(result)
    return [
        {
            "model_name": model,
            "questions": len(rows),
            "exact_accuracy_percent": round(100 * sum(bool(r["exact"]) for r in rows) / len(rows), 1),
            "mean_score_percent": round(100 * sum(float(r["score"]) for r in rows) / len(rows), 1),
            "errors": sum(bool(r.get("error")) for r in rows),
        }
        for model, rows in sorted(groups.items())
    ]


def subdomain_rows(run: dict) -> list[dict]:
    questions = {q["id"]: q for q in run.get("questions", [])}
    groups = defaultdict(list)
    for result in run.get("results", []):
        q = questions.get(result["question_id"], {})
        groups[(q.get("subdomain") or "Unspecified", result["model_name"])].append(result)
    return [
        {"subdomain": subdomain, "model_name": model,
         "mean_score_percent": 100 * sum(float(r["score"]) for r in rows) / len(rows)}
        for (subdomain, model), rows in sorted(groups.items())
    ]


def answer_text(question: dict, answers: list[str]) -> str:
    options = question.get("options", {})
    return ", ".join(f"{a}. {options.get(a, '')}" for a in answers) or "No parsed answer"


def gold_answers(question: dict) -> list[str]:
    if question.get("question_type") == "multiple_select":
        return list(question.get("correct_answers") or [])
    return [question["correct_answer"]] if question.get("correct_answer") else []


def result_status(rows: list[dict], expected_models: int) -> str:
    if rows and len(rows) == expected_models and all(bool(row.get("exact")) for row in rows):
        return "Consistently correct"
    if any(row.get("error") for row in rows):
        return "Call error"
    signatures = {tuple(row.get("parsed_answers") or []) for row in rows}
    if len(signatures) > 1:
        return "Models differ"
    return "Same incorrect answer"


def question_detail(qid: str, question: dict, rows: list[dict], status: str) -> str:
    options = "<br>".join(
        f"<b>{html.escape(str(k))}.</b> {html.escape(str(v))}" for k, v in question.get("options", {}).items()
    )
    result_rows = "".join(
        "<tr>" +
        f"<td>{html.escape(r['model_name'])}</td>" +
        f"<td>{html.escape(answer_text(question, r.get('parsed_answers') or []))}</td>" +
        f"<td>{100 * float(r.get('score', 0)):.1f}%</td>" +
        f"<td>{'Yes' if r.get('exact') else 'No'}</td>" +
        f"<td>{html.escape(r.get('error') or '')}</td></tr>" for r in rows
    )
    return (
        "<details><summary>" +
        f"<span class='qid'>{html.escape(qid)}</span>" +
        f"<span>{html.escape(question.get('subdomain') or 'Unspecified')}</span>" +
        f"<span class='qtext'>{html.escape(question.get('question', ''))}</span>" +
        f"<span class='status'>{html.escape(status)}</span></summary>" +
        "<div class='detail-grid'>" +
        f"<div><h4>Question and options</h4><p>{html.escape(question.get('question', ''))}</p><p>{options}</p></div>" +
        f"<div><h4>Gold answer</h4><p>{html.escape(answer_text(question, gold_answers(question)))}</p>" +
        f"<h4>Explanation</h4><p>{html.escape(question.get('explanation') or 'Not supplied')}</p></div></div>" +
        "<table><thead><tr><th>Model</th><th>Parsed answer</th><th>Score</th><th>Exact</th><th>Error</th></tr></thead>" +
        f"<tbody>{result_rows}</tbody></table></details>"
    )

def render_report(run: dict, title: str) -> str:
    summaries = summary_rows(run)
    models = [row["model_name"] for row in summaries]
    palette = ["#4c78a8", "#f58518", "#e45756", "#72b7b2", "#54a24b", "#b279a2"]
    colors = {model: palette[i % len(palette)] for i, model in enumerate(models)}
    summary_html = "".join(
        "<tr>" +
        f"<td><i class='swatch' style='background:{colors[r['model_name']]}'></i>{html.escape(r['model_name'])}</td>" +
        f"<td>{r['questions']}</td><td>{r['exact_accuracy_percent']:.1f}%</td>" +
        f"<td>{r['mean_score_percent']:.1f}%</td><td>{r['errors']}</td></tr>"
        for r in summaries
    )

    matrix = defaultdict(dict)
    for row in subdomain_rows(run):
        matrix[row["subdomain"]][row["model_name"]] = row["mean_score_percent"]
    chart_html = []
    for subdomain, values in matrix.items():
        bars = "".join(
            f"<div class='bar-slot'><div class='bar' style='height:{values.get(model, 0):.2f}%;background:{colors[model]}' "
            f"data-tip='{html.escape(model)} · {html.escape(subdomain)} · {values.get(model, 0):.1f}%'></div></div>"
            for model in models
        )
        chart_html.append(
            f"<div class='group'><div class='bars'>{bars}</div><div class='x-label'>{html.escape(subdomain)}</div></div>"
        )
    legend = "".join(
        f"<span><i style='background:{colors[m]}'></i>{html.escape(m)}</span>" for m in models
    )

    questions = {q["id"]: q for q in run.get("questions", [])}
    by_question = defaultdict(list)
    for result in run.get("results", []):
        by_question[result["question_id"]].append(result)
    details = []
    status_by_question = {}
    detail_by_question = {}
    for qid, question in questions.items():
        rows = by_question.get(qid, [])
        status = result_status(rows, len(models))
        status_by_question[qid] = status
        detail_by_question[qid] = question_detail(qid, question, rows, status)
        details.append(detail_by_question[qid])

    subdomain_sections = []
    for subdomain, values in matrix.items():
        domain_qids = [qid for qid, q in questions.items() if (q.get("subdomain") or "Unspecified") == subdomain]
        consistent = [qid for qid in domain_qids if status_by_question[qid] == "Consistently correct"][:5]
        problematic = [qid for qid in domain_qids if status_by_question[qid] == "Models differ"]
        problematic += [qid for qid in domain_qids if status_by_question[qid] in {"Same incorrect answer", "Call error"}]
        problematic = problematic[:5]
        mini_bars = "".join(
            f"<div class='mini-row'><span>{html.escape(model)}</span><div class='track'><i style='width:{values.get(model, 0):.2f}%;background:{colors[model]}'></i></div><b>{values.get(model, 0):.1f}%</b></div>"
            for model in models
        )
        correct_html = "".join(detail_by_question[qid] for qid in consistent) or "<p class='empty'>No consistently correct questions in this subdomain.</p>"
        problem_html = "".join(detail_by_question[qid] for qid in problematic) or "<p class='empty'>No inconsistent, incorrect, or call-error cases in this subdomain.</p>"
        subdomain_sections.append(
            f"<section class='domain-section'><h3>{html.escape(subdomain)}</h3><div class='mini-chart'>{mini_bars}</div>" +
            f"<div class='sample-grid'><div><h4>Consistently correct — up to 5</h4>{correct_html}</div>" +
            f"<div><h4>Inconsistent or incorrect — up to 5</h4>{problem_html}</div></div></section>"
        )

    return f"""<!doctype html><html lang='en'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'><title>{html.escape(title)}</title>
<style>
:root{{--ink:#252936;--muted:#667085;--line:#e4e7ec;--paper:#fff;--wash:#f7f8fa}}*{{box-sizing:border-box}}
body{{margin:0;background:var(--wash);color:var(--ink);font:15px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1500px;margin:auto;padding:42px 34px 80px}}h1{{font-size:38px;margin:0 0 8px}}h2{{font-size:28px;margin:48px 0 18px}}
.meta{{color:var(--muted);margin-bottom:24px}}.panel{{background:white;border:1px solid var(--line);border-radius:14px;padding:22px;box-shadow:0 2px 8px #1018280a;overflow:auto}}
table{{width:100%;border-collapse:collapse}}th,td{{padding:12px 14px;border-bottom:1px solid var(--line);text-align:left}}th{{background:#f9fafb;color:var(--muted)}}
.swatch,.legend i{{display:inline-block;width:12px;height:12px;margin-right:8px;border-radius:2px}}.chart{{height:430px;min-width:700px;display:flex;position:relative;padding-left:42px;border-left:1px solid var(--line);border-bottom:1px solid var(--line);background:repeating-linear-gradient(to top,transparent 0,transparent calc(20% - 1px),#e7eaf0 calc(20% - 1px),#e7eaf0 20%)}}
.y-axis{{position:absolute;left:0;top:0;height:360px;width:36px;display:flex;flex-direction:column;justify-content:space-between;text-align:right;color:var(--muted);font-size:12px}}.group{{min-width:150px;flex:1;display:flex;flex-direction:column;justify-content:flex-end}}.bars{{height:360px;display:flex;align-items:flex-end;justify-content:center;gap:7px;padding:0 12px}}.bar-slot{{height:100%;width:32px;display:flex;align-items:flex-end}}
.bar{{width:100%;min-height:1px;border-radius:4px 4px 0 0;position:relative}}.bar:hover:after{{content:attr(data-tip);position:absolute;bottom:calc(100% + 8px);left:50%;transform:translateX(-50%);background:#111827;color:white;padding:7px 9px;border-radius:6px;white-space:nowrap;z-index:5;font-size:12px}}
.x-label{{height:68px;padding:10px 6px 0;text-align:center;color:var(--muted);font-size:13px}}.legend{{display:flex;gap:22px;flex-wrap:wrap;margin-top:20px}}
.domain-section{{margin:28px 0 44px;padding:24px;background:white;border:1px solid var(--line);border-radius:14px}}.domain-section h3{{font-size:25px;margin:0 0 18px}}.mini-chart{{max-width:900px;margin-bottom:24px}}.mini-row{{display:grid;grid-template-columns:220px 1fr 64px;gap:12px;align-items:center;margin:10px 0}}.track{{height:20px;background:#edf0f4;border-radius:4px;overflow:hidden}}.track i{{display:block;height:100%}}.sample-grid{{display:block}}.sample-grid>div{{margin-top:28px}}.sample-grid>div+div{{padding-top:28px;border-top:2px solid var(--line)}}.empty{{padding:18px;background:#f7f8fa;color:var(--muted);border-radius:8px}}details{{background:white;border:1px solid var(--line);border-radius:10px;margin:10px 0;overflow:hidden}}summary{{display:grid;grid-template-columns:130px 190px 1fr 120px;gap:12px;align-items:center;padding:14px 18px;cursor:pointer}}
.qid{{font-family:ui-monospace,monospace}}.qtext{{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.status{{font-weight:650}}.detail-grid{{display:grid;grid-template-columns:1fr;gap:18px;padding:12px 22px;background:#fafafa;border-top:1px solid var(--line)}}
@media(max-width:900px){{summary{{grid-template-columns:1fr}}.detail-grid,.sample-grid{{grid-template-columns:1fr}}.mini-row{{grid-template-columns:1fr}}}}
</style></head><body><main><h1>{html.escape(title)}</h1>
<div class='meta'>Benchmark: {html.escape(str(run.get('benchmark_path', '')))}<br>Run: {html.escape(run.get('started_at', ''))} → {html.escape(run.get('finished_at', ''))}<br>Report generated: {datetime.now(timezone.utc).isoformat()}</div>
<h2>Model comparison</h2><section class='panel'><table><thead><tr><th>Model</th><th>Questions</th><th>Exact accuracy</th><th>Mean score</th><th>Errors</th></tr></thead><tbody>{summary_html}</tbody></table></section>
<h2>Mean score by subdomain</h2><section class='panel'><div class='chart'><div class='y-axis'><span>100</span><span>80</span><span>60</span><span>40</span><span>20</span><span>0</span></div>{''.join(chart_html)}</div><div class='legend'>{legend}</div></section>
<h2>Subdomain evidence samples</h2><p class='meta'>Each subdomain shows its own model plot, up to five consistently correct questions, and up to five model-difference, incorrect, or call-error cases.</p>{''.join(subdomain_sections)}<h2>All question-level evidence</h2><p class='meta'>Expand any row to inspect the question, gold answer, explanation, and each model result.</p>{''.join(details)}
</main></body></html>"""


def export_report(results: Path, output: Path, title: str, summary_csv: Path | None = None) -> None:
    run = json.loads(results.read_text(encoding="utf-8"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(run, title), encoding="utf-8")
    if summary_csv:
        rows = summary_rows(run)
        summary_csv.parent.mkdir(parents=True, exist_ok=True)
        with summary_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["model_name"])
            writer.writeheader(); writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a standalone DOVE HTML report from result JSON")
    parser.add_argument("--results", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", default="DOVE benchmark report")
    parser.add_argument("--summary-csv")
    args = parser.parse_args()
    export_report(Path(args.results), Path(args.output), args.title,
                  Path(args.summary_csv) if args.summary_csv else None)
    print(f"HTML report: {args.output}")


if __name__ == "__main__":
    main()



