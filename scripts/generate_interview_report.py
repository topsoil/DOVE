from __future__ import annotations

import argparse
import html
import json
from collections import defaultdict
from pathlib import Path


PALETTE = ["#386cb0", "#f28e2b", "#59a14f", "#e15759", "#9c755f", "#b07aa1", "#007681", "#edc949", "#76b7b2"]


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def aggregate(run: dict):
    question_by_id = {q["id"]: q for q in run["questions"]}
    models = [m["name"] for m in run["models"]]
    overall = defaultdict(list)
    by_benchmark = defaultdict(list)
    by_dimension = defaultdict(list)
    for result in run["results"]:
        model = result["model_name"]
        overall[model].append(float(result["score"]))
        by_benchmark[(result["benchmark_id"], model)].append(float(result["score"]))
        for dimension, score in result.get("dimension_scores", {}).items():
            by_dimension[(dimension, model)].append(float(score))
    mean = lambda rows: sum(rows) / len(rows) if rows else 0.0
    return question_by_id, models, {m: mean(v) for m, v in overall.items()}, \
        {k: mean(v) for k, v in by_benchmark.items()}, {k: mean(v) for k, v in by_dimension.items()}


def operating_boundary(score: float) -> str:
    if score >= .80:
        return "High rubric coverage; candidate for supervised analytical assistance after expert validation."
    if score >= .65:
        return "Moderate coverage; use with domain review and explicit evidence checks."
    if score >= .45:
        return "Restricted role: drafting, extraction, or retrieval with line-by-line review."
    return "Do not rely on this model for independent biomedical interpretation."


def bar(value: float, color: str) -> str:
    return f"<div class='track'><i style='width:{100*value:.1f}%;background:{color}'></i></div><b>{pct(value)}</b>"


def render_report(run: dict) -> str:
    questions, models, overall, by_benchmark, by_dimension = aggregate(run)
    colors = {model: PALETTE[i % len(PALETTE)] for i, model in enumerate(models)}
    categories = list(dict.fromkeys(q["benchmark_id"] for q in run["questions"]))
    dimensions = sorted({d for result in run["results"] for d in result.get("dimension_scores", {})})
    summary = "".join(
        f"<tr><td><i class='swatch' style='background:{colors[m]}'></i>{html.escape(m)}</td>"
        f"<td>{pct(overall.get(m,0))}</td><td>{html.escape(operating_boundary(overall.get(m,0)))}</td></tr>"
        for m in models
    )
    category_rows = "".join(
        "<tr><th>" + html.escape(category) + "</th>" +
        "".join(f"<td>{pct(by_benchmark.get((category,m),0))}</td>" for m in models) + "</tr>"
        for category in categories
    )
    dimension_rows = "".join(
        "<tr><th>" + html.escape(d.replace("_", " ").title()) + "</th>" +
        "".join(f"<td>{pct(by_dimension.get((d,m),0))}</td>" for m in models) + "</tr>"
        for d in dimensions
    )
    model_headers = "".join(f"<th>{html.escape(m)}</th>" for m in models)

    candidate_sections = []
    for model in models:
        rows = [r for r in run["results"] if r["model_name"] == model]
        low = sorted(rows, key=lambda r: r["score"])[:8]
        flags = sum(len(r.get("triggered_red_flags", [])) for r in rows)
        category_bars = "".join(
            f"<div class='metric'><span>{html.escape(c)}</span>{bar(by_benchmark.get((c,model),0),colors[model])}</div>"
            for c in categories
        )
        evidence = []
        for result in low:
            q = questions[result["question_id"]]
            missing = [c["description"] for c in result.get("criteria", []) if not c["matched"]]
            response = result.get("response", {})
            evidence.append(
                "<details><summary>" + html.escape(result["question_id"]) +
                f" · {pct(float(result['score']))} · " + html.escape(q["category"]) + "</summary>"
                f"<h4>Interview question</h4><p>{html.escape(q['prompt'])}</p>"
                f"<h4>Candidate answer</h4><p>{html.escape(response.get('answer',''))}</p>"
                f"<h4>Uncertainty</h4><p>{html.escape(response.get('uncertainty',''))}</p>"
                f"<h4>Reference answer</h4><p>{html.escape(q['reference_answer'])}</p>"
                f"<h4>Missing rubric concepts</h4><ul>{''.join('<li>'+html.escape(x)+'</li>' for x in missing) or '<li>None</li>'}</ul>"
                f"<h4>Grounding</h4><p>{html.escape(q['source_rationale'])}</p>"
                f"<p>Source IDs: {html.escape(', '.join(q['source_ids']))}</p></details>"
            )
        candidate_sections.append(
            f"<section class='candidate'><h2>{html.escape(model)}</h2>"
            f"<p class='boundary'>{html.escape(operating_boundary(overall.get(model,0)))}</p>"
            f"<p>Overall rubric coverage: <b>{pct(overall.get(model,0))}</b> · Triggered red flags: <b>{flags}</b></p>"
            f"{category_bars}<h3>Lowest-scoring evidence</h3>{''.join(evidence)}</section>"
        )
    sources = "".join(
        f"<li id='{html.escape(s['id'])}'><b>{html.escape(s['id'])}</b> — "
        f"<a href='{html.escape(s['url'])}'>{html.escape(s['title'])}</a> ({html.escape(s['organization'])})</li>"
        for s in run["sources"]
    )
    return f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>{html.escape(run['suite_name'])}</title><style>
:root{{--ink:#20242e;--muted:#667085;--line:#dfe3ea;--wash:#f4f6f8}}*{{box-sizing:border-box}}body{{margin:0;background:var(--wash);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,sans-serif}}main{{max-width:1280px;margin:auto;padding:42px 30px 80px}}h1{{font-size:40px;margin:0}}h2{{margin-top:42px;font-size:28px}}.lede,.note{{color:var(--muted)}}.panel,.candidate{{background:white;border:1px solid var(--line);border-radius:14px;padding:24px;margin:22px 0;box-shadow:0 2px 8px #1018280a;overflow:auto}}table{{border-collapse:collapse;width:100%;min-width:700px}}th,td{{padding:12px;border-bottom:1px solid var(--line);text-align:left}}thead th{{background:#f8fafc}}.swatch{{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:8px}}.boundary{{font-size:17px;padding:14px;background:#f5f7fa;border-left:5px solid #65758b}}.metric{{display:grid;grid-template-columns:280px 1fr 70px;gap:12px;align-items:center;margin:10px 0}}.track{{height:20px;background:#e9edf2;border-radius:5px;overflow:hidden}}.track i{{height:100%;display:block}}details{{border:1px solid var(--line);border-radius:9px;margin:10px 0;padding:0 18px 16px}}summary{{cursor:pointer;font-weight:650;padding:15px 0}}a{{color:#2457a7}}@media(max-width:760px){{.metric{{grid-template-columns:1fr}}}}
</style></head><body><main><h1>{html.escape(run['suite_name'])}</h1><p class='lede'>Progressive biomedical and bioinformatics virtual-scientist interview · {len(run['questions'])} questions · {len(models)} models</p>
<p class='note'><b>Interpretation:</b> {html.escape(run['scoring_note'])} Items are source-grounded drafts until domain experts approve them.</p>
<section class='panel'><h2>Candidate summary</h2><table><thead><tr><th>Model</th><th>Rubric coverage</th><th>Suggested operating boundary</th></tr></thead><tbody>{summary}</tbody></table></section>
<section class='panel'><h2>Interview-level matrix</h2><table><thead><tr><th>Benchmark</th>{model_headers}</tr></thead><tbody>{category_rows}</tbody></table></section>
<section class='panel'><h2>Capability matrix</h2><table><thead><tr><th>Dimension</th>{model_headers}</tr></thead><tbody>{dimension_rows}</tbody></table></section>
{''.join(candidate_sections)}<section class='panel'><h2>Authoritative source catalog</h2><ol>{sources}</ol></section></main></body></html>"""


def export_interview_report(run: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(run), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run = json.loads(Path(args.results).read_text(encoding="utf-8"))
    export_interview_report(run, Path(args.output))
    print(f"HTML report: {args.output}")


if __name__ == "__main__":
    main()

