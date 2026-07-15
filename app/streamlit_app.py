from __future__ import annotations

import json
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dove.benchmark_loader import load_benchmark
from dove.benchmark_runner import run_benchmark
from dove.model_clients import list_ollama_models
from dove.schemas import BenchmarkItem, ModelConfig

st.set_page_config(page_title="DOVEboard", page_icon="🕊️", layout="wide")
st.title("🕊️ DOVEboard")
st.caption("Domain-Oriented AI/LLMs Validation & Evaluation")


def result_view(run: dict) -> None:
    questions = pd.DataFrame(run.get("questions", []))
    results = pd.DataFrame(run.get("results", []))
    if results.empty:
        st.warning("The result file contains no model results.")
        return

    question_cols = [c for c in [
        "id", "domain", "subdomain", "difficulty", "question_type",
        "review_status", "question", "options", "correct_answer",
        "correct_answers", "explanation", "tags"] if c in questions]
    frame = results.merge(
        questions[question_cols], left_on="question_id", right_on="id", how="left")
    frame["correctness"] = frame["exact"].map({True: "correct", False: "incorrect"})

    filters = st.columns(4)
    for index, column in enumerate(["model_name", "domain", "subdomain", "difficulty"]):
        if column in frame:
            choices = sorted(str(x) for x in frame[column].dropna().unique())
            selected = filters[index].multiselect(
                column.replace("_", " ").title(), choices, key=f"result_filter_{column}")
            if selected:
                frame = frame[frame[column].astype(str).isin(selected)]
    filters2 = st.columns(4)
    for index, column in enumerate(["question_type", "review_status", "correctness"]):
        if column in frame:
            choices = sorted(str(x) for x in frame[column].dropna().unique())
            selected = filters2[index].multiselect(
                column.replace("_", " ").title(), choices, key=f"result_filter_{column}")
            if selected:
                frame = frame[frame[column].astype(str).isin(selected)]
    tag = filters2[3].text_input("Tag contains", key="result_tag")
    if tag and "tags" in frame:
        frame = frame[frame["tags"].apply(
            lambda values: tag.lower() in " ".join(
                values if isinstance(values, list) else []).lower())]
    if frame.empty:
        st.warning("No results match the current filters.")
        return

    summary = frame.groupby("model_name").agg(
        questions=("question_id", "count"),
        exact_accuracy=("exact", "mean"),
        mean_score=("score", "mean"),
        errors=("error", lambda values: values.notna().sum()),
    ).reset_index()
    summary["exact_accuracy"] = (summary["exact_accuracy"] * 100).round(1)
    summary["mean_score"] = (summary["mean_score"] * 100).round(1)
    summary = summary.rename(columns={
        "exact_accuracy": "exact_accuracy_percent",
        "mean_score": "mean_score_percent"})

    st.subheader("Model comparison")
    st.dataframe(summary, width="stretch", hide_index=True)
    st.download_button(
        "Download summary CSV", summary.to_csv(index=False),
        "dove_summary.csv", "text/csv")

    model_order = sorted(frame["model_name"].unique())

    if {"subdomain", "model_name", "score"} <= set(frame):
        st.subheader("Mean score by subdomain")
        chart_data = (
            frame.groupby(["subdomain", "model_name"], as_index=False)["score"]
            .mean()
            .rename(columns={"score": "score_percent"})
        )
        chart_data["score_percent"] = (chart_data["score_percent"] * 100).round(1)
        subdomain_order = sorted(chart_data["subdomain"].dropna().unique())
        score_chart = (
            alt.Chart(chart_data)
            .mark_bar()
            .encode(
                x=alt.X(
                    "subdomain:N", sort=subdomain_order,
                    axis=alt.Axis(title=None, labelAngle=-30, labelLimit=170)),
                xOffset=alt.XOffset("model_name:N", sort=model_order),
                y=alt.Y(
                    "score_percent:Q",
                    scale=alt.Scale(domain=[0, 100], clamp=True),
                    axis=alt.Axis(
                        title="Mean score (%)",
                        values=[0, 20, 40, 60, 80, 100])),
                color=alt.Color(
                    "model_name:N", sort=model_order,
                    scale=alt.Scale(scheme="tableau10"),
                    legend=alt.Legend(title="Model", orient="bottom")),
                tooltip=[
                    alt.Tooltip("subdomain:N", title="Subdomain"),
                    alt.Tooltip("model_name:N", title="Model"),
                    alt.Tooltip(
                        "score_percent:Q", title="Mean score", format=".1f"),
                ],
            )
            .properties(height=360)
        )
        st.altair_chart(score_chart, width="stretch")
        st.caption(
            "Grouped bars use a shared 0–100% axis; colors remain stable by model.")

    def option_text(options, labels) -> str:
        option_map = options if isinstance(options, dict) else {}
        values = labels if isinstance(labels, list) else []
        if not values:
            return "No parsed answer"
        return ", ".join(
            f"{label}: {option_map.get(label, 'Unknown option')}" for label in values)

    question_rows = []
    for question_id, group in frame.groupby("question_id", sort=True):
        first = group.iloc[0]
        options = first.get("options") if isinstance(first.get("options"), dict) else {}
        gold_labels = (
            [first.get("correct_answer")]
            if first.get("question_type") == "single_choice"
            else list(first.get("correct_answers") or [])
        )
        gold_labels = [label for label in gold_labels if label]
        signatures = {
            tuple(sorted(value if isinstance(value, list) else []))
            for value in group["parsed_answers"]
        }
        agreement = len(signatures) == 1
        all_correct = bool(group["exact"].all())
        if agreement and all_correct:
            status = "Agree — all correct"
        elif agreement:
            status = "Agree — same incorrect answer"
        else:
            status = "Disagree"

        answer_lines = []
        answer_by_model = {}
        for _, model_row in group.sort_values("model_name").iterrows():
            parsed = (
                model_row["parsed_answers"]
                if isinstance(model_row["parsed_answers"], list) else [])
            answer = option_text(options, parsed)
            score = float(model_row["score"]) * 100
            error = f" · ERROR: {model_row['error']}" if model_row.get("error") else ""
            formatted = f"{answer} ({score:.0f}%){error}"
            answer_by_model[model_row["model_name"]] = formatted
            answer_lines.append(f"{model_row['model_name']}: {formatted}")

        question = str(first.get("question") or "")
        question_row = {
            "question_id": question_id,
            "subdomain": first.get("subdomain") or "",
            "status": status,
            "question": question,
            "gold_answer": option_text(options, gold_labels),
            "model_answers": " | ".join(answer_lines),
            "explanation": first.get("explanation") or "",
            "display": f"{status} · {question_id} · {question[:72]}",
            "bar": 1,
        }
        for model_index, model_name in enumerate(model_order, 1):
            question_row[f"model_answer_{model_index}"] = answer_by_model.get(
                model_name, "No result")
        question_rows.append(question_row)

    overview = pd.DataFrame(question_rows)
    st.subheader("Question agreement explorer")
    st.caption(
        "Hover over a colored row to see the full question, gold answer, "
        "each model's answer and score, and the explanation.")

    control_a, control_b, control_c = st.columns([2, 1, 1])
    status_choices = list(overview["status"].drop_duplicates())
    selected_status = control_a.multiselect(
        "Agreement status", status_choices, default=status_choices,
        key="agreement_status")
    page_size = control_b.selectbox(
        "Rows per page", [10, 15, 20, 25], index=1, key="agreement_page_size")
    visible = overview[overview["status"].isin(selected_status)].reset_index(drop=True)
    page_count = max(1, (len(visible) + page_size - 1) // page_size)
    page = control_c.number_input(
        "Page", min_value=1, max_value=page_count, value=1,
        key="agreement_page")
    start = (int(page) - 1) * page_size
    page_data = visible.iloc[start:start + page_size].copy()
    control_c.caption(f"of {page_count}")

    if page_data.empty:
        st.info("No questions match the selected agreement statuses.")
    else:
        status_domain = [
            "Agree — all correct", "Agree — same incorrect answer", "Disagree"]
        status_range = ["#2E8B57", "#C54B4B", "#E69F00"]
        answer_tooltips = [
            alt.Tooltip(
                f"model_answer_{model_index}:N", title=model_name)
            for model_index, model_name in enumerate(model_order, 1)
        ]
        agreement_tooltips = [
            alt.Tooltip("question_id:N", title="Question ID"),
            alt.Tooltip("status:N", title="Agreement"),
            alt.Tooltip("subdomain:N", title="Subdomain"),
            alt.Tooltip("question:N", title="Question"),
            alt.Tooltip("gold_answer:N", title="Gold answer"),
        ] + answer_tooltips + [
            alt.Tooltip("explanation:N", title="Explanation"),
        ]
        agreement_chart = (
            alt.Chart(page_data)
            .mark_bar(size=22, cornerRadius=3)
            .encode(
                x=alt.X("bar:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
                y=alt.Y(
                    "display:N", sort=list(page_data["display"]),
                    axis=alt.Axis(title=None, labelLimit=650)),
                color=alt.Color(
                    "status:N",
                    scale=alt.Scale(domain=status_domain, range=status_range),
                    legend=alt.Legend(title="Agreement", orient="bottom")),
                tooltip=agreement_tooltips,
            )
            .properties(height=max(220, len(page_data) * 34))
        )
        st.altair_chart(agreement_chart, width="stretch")
        st.download_button(
            "Download question-level summary CSV",
            visible.drop(columns=["bar"]).to_csv(index=False),
            "dove_question_summary.csv", "text/csv")

    with st.expander("Show raw model-level rows"):
        display_cols = [c for c in [
            "question_id", "model_name", "subdomain", "question", "options",
            "correct_answer", "correct_answers", "parsed_answers", "score",
            "raw_response", "explanation", "error"] if c in frame]
        st.dataframe(
            frame[display_cols], width="stretch", height=420, hide_index=True)


run_tab, results_tab, curation_tab = st.tabs(
    ["Configure & run", "Results comparison", "Candidate curation"])

with run_tab:
    st.subheader("1. Choose a benchmark")
    builtins = {
        "Bioinformatics best practices — 100 source-attributed drafts":
            ROOT / "data" / "benchmarks" / "bioinformatics_best_practices_100.json",
        "Disease genetics — 100 source-attributed drafts":
            ROOT / "data" / "benchmarks" / "disease_genetics_100.json",
        "DIMI Lab published-paper pilot — 60 source-grounded drafts":
            ROOT / "data" / "benchmarks" / "dimi_lab_60.json",
        "Small bioinformatics example — 2 questions":
            ROOT / "data" / "benchmarks" / "bioinformatics_v0_1.json",
    }
    source_choice = st.radio(
        "Benchmark source", ["Included benchmark", "Upload JSON/YAML"],
        horizontal=True, label_visibility="collapsed")
    items: list[BenchmarkItem] = []
    benchmark_name = ""
    if source_choice == "Included benchmark":
        label = st.selectbox("Included benchmark", list(builtins))
        benchmark_path = builtins[label]
        benchmark_name = str(benchmark_path)
        if benchmark_path.exists():
            items = load_benchmark(benchmark_path)
        else:
            st.warning("This benchmark has not been generated yet.")
    else:
        uploaded_benchmark = st.file_uploader(
            "Benchmark file", type=["json", "yaml", "yml"], key="run_benchmark_upload")
        if uploaded_benchmark:
            try:
                raw = uploaded_benchmark.getvalue().decode("utf-8")
                import yaml
                data = yaml.safe_load(raw)
                if isinstance(data, dict):
                    data = data.get("questions", data.get("items"))
                items = [BenchmarkItem.model_validate(item) for item in data]
                benchmark_name = uploaded_benchmark.name
            except Exception as exc:
                st.error(f"Could not load benchmark: {exc}")
    if items:
        subdomains = sorted({item.subdomain for item in items if item.subdomain})
        st.caption(f"{len(items)} questions · {len(subdomains)} subdomains")
        if any(item.review_status not in {"expert_reviewed", "consensus_reviewed"} for item in items):
            st.warning("This included set is an AI-drafted, source-attributed pilot benchmark. Use it for model comparison, not clinical validation, until domain experts review it.")
        with st.expander("Preview benchmark"):
            preview_rows = []
            for item in items:
                options_text = " | ".join(
                    f"{label}: {text}" for label, text in item.options.items())
                gold_labels = (
                    [item.correct_answer]
                    if item.question_type == "single_choice"
                    else list(item.correct_answers or [])
                )
                gold_text = ", ".join(
                    f"{label}: {item.options.get(label, 'Unknown option')}"
                    for label in gold_labels if label)
                type_label = item.question_type.replace("_", " ").title()
                preview_rows.append({
                    "id": item.id,
                    "subdomain": item.subdomain or "",
                    "type": type_label,
                    "difficulty": item.difficulty or "",
                    "question": item.question,
                    "options": options_text,
                    "gold_answer": gold_text,
                    "explanation": item.explanation or "",
                    "source": item.source,
                    "display": (
                        f"{item.id} · {type_label} · "
                        f"{item.question[:68]}"),
                    "bar": 1,
                })
            preview = pd.DataFrame(preview_rows)
            preview_a, preview_b = st.columns([1, 1])
            preview_page_size = preview_a.selectbox(
                "Preview rows per page", [10, 15, 20, 25], index=1,
                key="preview_page_size")
            preview_page_count = max(
                1, (len(preview) + preview_page_size - 1) // preview_page_size)
            if st.session_state.get("preview_page", 1) > preview_page_count:
                st.session_state["preview_page"] = 1
            preview_page = preview_b.number_input(
                "Preview page", min_value=1, max_value=preview_page_count,
                value=1, key="preview_page")
            preview_b.caption(f"of {preview_page_count}")
            preview_start = (int(preview_page) - 1) * preview_page_size
            preview_page_data = preview.iloc[
                preview_start:preview_start + preview_page_size]
            preview_chart = (
                alt.Chart(preview_page_data)
                .mark_bar(size=22, cornerRadius=3)
                .encode(
                    x=alt.X(
                        "bar:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
                    y=alt.Y(
                        "display:N", sort=list(preview_page_data["display"]),
                        axis=alt.Axis(title=None, labelLimit=650)),
                    color=alt.Color(
                        "type:N",
                        scale=alt.Scale(scheme="set2"),
                        legend=alt.Legend(
                            title="Question type", orient="bottom")),
                    tooltip=[
                        alt.Tooltip("id:N", title="Question ID"),
                        alt.Tooltip("subdomain:N", title="Subdomain"),
                        alt.Tooltip("type:N", title="Question type"),
                        alt.Tooltip("difficulty:N", title="Difficulty"),
                        alt.Tooltip("question:N", title="Question"),
                        alt.Tooltip("options:N", title="Options"),
                        alt.Tooltip("gold_answer:N", title="Gold answer"),
                        alt.Tooltip("explanation:N", title="Explanation"),
                        alt.Tooltip("source:N", title="Source"),
                    ],
                )
                .properties(height=max(220, len(preview_page_data) * 34))
            )
            st.altair_chart(preview_chart, width="stretch")
            st.caption(
                "Hover over a row to inspect the full question, choices, "
                "gold answer, explanation, and source.")


    st.subheader("2. Select models")
    st.caption("Keys stay in this Streamlit session and are excluded from saved results.")

    ollama_col, remote_col = st.columns(2)
    selected_ollama: list[str] = []
    with ollama_col:
        st.markdown("#### Local Ollama")
        ollama_url = st.text_input("Ollama URL", "http://localhost:11434")
        if st.button("Discover installed Ollama models"):
            try:
                st.session_state["ollama_models"] = list_ollama_models(ollama_url)
                st.success(f"Found {len(st.session_state['ollama_models'])} models.")
            except Exception as exc:
                st.session_state["ollama_models"] = []
                st.error(f"Could not reach Ollama: {exc}")
        available = [
            model.get("name") or model.get("model")
            for model in st.session_state.get("ollama_models", [])]
        selected_ollama = st.multiselect(
            "Models to compare", [value for value in available if value])
        manual_models = st.text_input(
            "Additional model names", placeholder="llama3.1:8b, qwen3:8b")
        selected_ollama.extend(
            value.strip() for value in manual_models.split(",") if value.strip())
        selected_ollama = list(dict.fromkeys(selected_ollama))

    with remote_col:
        st.markdown("#### OpenAI-compatible API")
        use_remote = st.checkbox("Add a remote/BYOK model")
        remote_name = st.text_input("Display name", "remote-model",
                                    disabled=not use_remote)
        remote_url = st.text_input("Base URL", "https://api.openai.com/v1",
                                   disabled=not use_remote)
        remote_model = st.text_input("Model ID", disabled=not use_remote,
                                     placeholder="provider model ID")
        remote_key = st.text_input("API key", type="password", disabled=not use_remote,
                                   help="Used in memory for this run; never written to result JSON.")
        st.caption("OpenAI-compatible means POST /chat/completions with Bearer authentication.")

    temperature = st.slider("Temperature", 0.0, 1.0, 0.0, 0.1)
    models = [
        ModelConfig(name=f"ollama:{name}", provider="ollama", base_url=ollama_url,
                    model=name, temperature=temperature)
        for name in selected_ollama]
    if use_remote and remote_model:
        models.append(ModelConfig(
            name=remote_name or remote_model, provider="openai_compatible",
            base_url=remote_url, model=remote_model, api_key=remote_key or None,
            temperature=temperature))

    st.subheader("3. Run and compare")
    max_questions = max(1, len(items))
    question_limit = st.number_input(
        "Questions to run", min_value=1, max_value=max_questions,
        value=max_questions, disabled=not items)
    estimated = int(question_limit) * len(models)
    st.caption(f"{len(models)} model(s) selected · {estimated} total model calls")

    if st.button("Run benchmark", type="primary", disabled=not (items and models)):
        selected_items = items[:int(question_limit)]
        progress_bar = st.progress(0.0)
        status = st.empty()

        def update_progress(done: int, total: int, model_name: str, question_id: str):
            progress_bar.progress(done / total if total else 1.0)
            status.caption(f"{done}/{total} · {model_name} · {question_id}")

        with st.spinner("Running benchmark…"):
            run = run_benchmark(
                selected_items, models, benchmark_name, progress=update_progress)
        st.session_state["latest_run"] = run.model_dump()
        status.success(f"Completed {len(run.results)} model-question evaluations.")
        st.download_button(
            "Download full result JSON",
            json.dumps(run.model_dump(), indent=2),
            "dove_results.json", "application/json")
        st.info("Open the Results comparison tab to explore scores and disagreements.")

with results_tab:
    uploaded_result = st.file_uploader(
        "Load a DOVE result JSON", type=["json"], key="results_upload")
    active_run = None
    if uploaded_result:
        active_run = json.load(uploaded_result)
    elif st.session_state.get("latest_run"):
        active_run = st.session_state["latest_run"]
        st.caption("Showing the latest benchmark run from this session.")
        st.download_button(
            "Download full result JSON",
            json.dumps(active_run, indent=2),
            "dove_results.json", "application/json", key="result_download")
    if active_run:
        result_view(active_run)
    else:
        st.info("Run a benchmark or upload a previous DOVE result.")

with curation_tab:
    candidate_file = st.file_uploader(
        "Load generated candidate questions", type=["json"], key="candidates")
    st.info("Generated questions are not benchmark gold until a human approves them.")
    if candidate_file:
        candidates = json.load(candidate_file)
        rows = [{
            "approve": False, "id": item.get("id"), "question": item.get("question"),
            "type": item.get("question_type"),
            "answer": item.get("correct_answer")
                or ", ".join(item.get("correct_answers") or []),
            "explanation": item.get("explanation"), "source": item.get("source"),
            "provenance": json.dumps(item.get("provenance", {})),
        } for item in candidates]
        edited = st.data_editor(
            pd.DataFrame(rows), width="stretch",
            disabled=["id", "question", "type", "answer", "explanation",
                      "source", "provenance"], hide_index=True)
        approved_ids = set(edited.loc[edited["approve"], "id"]) if rows else set()
        status_value = st.selectbox(
            "Approval status", ["expert_reviewed", "consensus_reviewed"])
        approved = []
        for item in candidates:
            if item.get("id") in approved_ids:
                value = dict(item)
                value["review_status"] = status_value
                approved.append(value)
        st.download_button(
            "Export approved benchmark JSON", json.dumps(approved, indent=2),
            "approved_benchmark.json", "application/json", disabled=not approved)








