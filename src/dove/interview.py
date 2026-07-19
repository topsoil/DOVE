from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal

from pydantic import BaseModel, Field, model_validator

from .model_clients import chat
from .schemas import ModelConfig, ReviewStatus


Dimension = Literal[
    "biomedical_knowledge", "bioinformatics_fundamentals", "best_practice_awareness",
    "scientific_reasoning", "evidence_grounding", "hallucination_resistance",
    "workflow_planning", "uncertainty_calibration",
]


class SourceReference(BaseModel):
    id: str
    title: str
    organization: str
    url: str
    kind: str = "guideline"


class RubricCriterion(BaseModel):
    id: str
    dimension: Dimension
    description: str
    match_any: list[str]
    weight: float = 1.0


class RedFlag(BaseModel):
    description: str
    match_any: list[str]
    penalty: float = 0.2


class InterviewItem(BaseModel):
    id: str
    benchmark_id: str
    level: int = Field(ge=1, le=7)
    category: str
    domain: str
    prompt: str
    reference_answer: str
    rubric: list[RubricCriterion]
    source_ids: list[str]
    source_rationale: str
    follow_up_prompt: str | None = None
    red_flags: list[RedFlag] = Field(default_factory=list)
    difficulty: str = "intermediate"
    review_status: ReviewStatus = "draft"
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_rubric(self):
        if not self.rubric:
            raise ValueError("interview item requires at least one rubric criterion")
        if any(not criterion.match_any for criterion in self.rubric):
            raise ValueError("each rubric criterion requires match_any phrases")
        return self


class InterviewResponse(BaseModel):
    answer: str = ""
    uncertainty: str = ""
    recommended_next_steps: list[str] = Field(default_factory=list)
    citations_or_sources: list[str] = Field(default_factory=list)


class InterviewResult(BaseModel):
    question_id: str
    benchmark_id: str
    model_name: str
    raw_response: str
    response: InterviewResponse
    follow_up_raw_response: str = ""
    follow_up_response: InterviewResponse | None = None
    score: float
    dimension_scores: dict[str, float]
    criteria: list[dict]
    triggered_red_flags: list[str] = Field(default_factory=list)
    error: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model_metadata: dict = Field(default_factory=dict)


class InterviewRun(BaseModel):
    suite_name: str
    started_at: str
    finished_at: str
    sources: list[SourceReference]
    models: list[dict]
    questions: list[InterviewItem]
    results: list[InterviewResult]
    scoring_note: str = (
        "Scores are deterministic rubric-coverage indicators, not substitutes for expert adjudication."
    )


def load_sources(path: str | Path) -> list[SourceReference]:
    return [SourceReference.model_validate(x) for x in json.loads(Path(path).read_text(encoding="utf-8"))]


def load_interview_benchmark(path: str | Path) -> list[InterviewItem]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = payload.get("items", payload) if isinstance(payload, dict) else payload
    return [InterviewItem.model_validate(row) for row in rows]


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _contains(text: str, phrase: str) -> bool:
    normalized = _normalize(phrase)
    return bool(normalized) and normalized in text


def parse_interview_response(raw: str) -> InterviewResponse:
    text = raw.strip()
    candidates = [text]
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                if "answer" not in data:
                    data["answer"] = data.get("response", data.get("analysis", ""))
                return InterviewResponse.model_validate(data)
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    return InterviewResponse(answer=text)


def score_interview_response(item: InterviewItem, response: InterviewResponse,
                             follow_up: InterviewResponse | None = None) -> tuple[float, dict[str, float], list[dict], list[str]]:
    combined = " ".join([
        response.answer, response.uncertainty, " ".join(response.recommended_next_steps),
        " ".join(response.citations_or_sources),
        follow_up.answer if follow_up else "", follow_up.uncertainty if follow_up else "",
        " ".join(follow_up.recommended_next_steps) if follow_up else "",
    ])
    normalized = _normalize(combined)
    total_weight = sum(c.weight for c in item.rubric)
    earned = 0.0
    by_dimension = defaultdict(lambda: [0.0, 0.0])
    criteria = []
    for criterion in item.rubric:
        matched_phrase = next((phrase for phrase in criterion.match_any if _contains(normalized, phrase)), None)
        matched = matched_phrase is not None
        earned += criterion.weight if matched else 0.0
        by_dimension[criterion.dimension][1] += criterion.weight
        if matched:
            by_dimension[criterion.dimension][0] += criterion.weight
        criteria.append({
            "id": criterion.id, "dimension": criterion.dimension,
            "description": criterion.description, "matched": matched,
            "matched_phrase": matched_phrase, "weight": criterion.weight,
        })
    triggered = []
    penalty = 0.0
    for flag in item.red_flags:
        if any(_contains(normalized, phrase) for phrase in flag.match_any):
            triggered.append(flag.description)
            penalty += flag.penalty
    score = max(0.0, min(1.0, (earned / total_weight if total_weight else 0.0) - penalty))
    dimensions = {name: earned_weight / weight for name, (earned_weight, weight) in by_dimension.items()}
    return score, dimensions, criteria, triggered


def interview_prompt(item: InterviewItem) -> str:
    return (
        "You are being interviewed for a biomedical/bioinformatics virtual scientist role. "
        "Answer the scenario directly. Distinguish facts, assumptions, and recommendations. "
        "Do not invent citations or evidence. State what you would verify before a clinical or scientific decision.\n\n"
        f"Question: {item.prompt}\n\n"
        "Return one JSON object with exactly these fields: "
        '{"answer":"...","uncertainty":"...","recommended_next_steps":["..."],'
        '"citations_or_sources":["source names you genuinely know; otherwise say source lookup needed"]}'
    )


ProgressCallback = Callable[[int, int, str, str], None]


def run_interview(items: list[InterviewItem], models: list[ModelConfig], sources: list[SourceReference],
                  suite_name: str, run_followups: bool = False,
                  progress: ProgressCallback | None = None) -> InterviewRun:
    started = datetime.now(timezone.utc).isoformat()
    results: list[InterviewResult] = []
    total = len(items) * len(models)
    completed = 0
    for model in models:
        for item in items:
            if progress:
                progress(completed, total, model.name, item.id)
            try:
                raw, metadata = chat(model, [{"role": "user", "content": interview_prompt(item)}])
                response = parse_interview_response(raw)
                follow_raw = ""
                follow_response = None
                if run_followups and item.follow_up_prompt:
                    follow_raw, follow_meta = chat(model, [
                        {"role": "user", "content": interview_prompt(item)},
                        {"role": "assistant", "content": raw},
                        {"role": "user", "content": (
                            f"Follow-up: {item.follow_up_prompt}\nReturn the same JSON structure. "
                            "Correct your earlier answer if the follow-up exposes a problem."
                        )},
                    ])
                    follow_response = parse_interview_response(follow_raw)
                    metadata["follow_up"] = follow_meta
                score, dimensions, criteria, flags = score_interview_response(item, response, follow_response)
                results.append(InterviewResult(
                    question_id=item.id, benchmark_id=item.benchmark_id, model_name=model.name,
                    raw_response=raw, response=response, follow_up_raw_response=follow_raw,
                    follow_up_response=follow_response, score=score, dimension_scores=dimensions,
                    criteria=criteria, triggered_red_flags=flags, model_metadata=metadata,
                ))
            except Exception as exc:
                results.append(InterviewResult(
                    question_id=item.id, benchmark_id=item.benchmark_id, model_name=model.name,
                    raw_response="", response=InterviewResponse(), score=0.0, dimension_scores={},
                    criteria=[], error=f"{type(exc).__name__}: {exc}",
                ))
            completed += 1
            if progress:
                progress(completed, total, model.name, item.id)
    return InterviewRun(
        suite_name=suite_name, started_at=started,
        finished_at=datetime.now(timezone.utc).isoformat(), sources=sources,
        models=[m.model_dump(exclude={"api_key_env", "api_key"}) for m in models],
        questions=items, results=results,
    )


def save_interview_run(run: InterviewRun, output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(run.model_dump(), indent=2), encoding="utf-8")
