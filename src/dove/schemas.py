from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, SecretStr, model_validator

QuestionType = Literal["single_choice", "multiple_select"]
ReviewStatus = Literal[
    "draft", "llm_generated", "corpus_generated", "expert_reviewed",
    "consensus_reviewed", "retired",
]


class BenchmarkItem(BaseModel):
    id: str
    domain: str
    subdomain: str | None = None
    question_type: QuestionType
    question: str
    options: dict[str, str]
    correct_answer: str | None = None
    correct_answers: list[str] | None = None
    explanation: str | None = None
    difficulty: str | None = None
    tags: list[str] = Field(default_factory=list)
    source: str = "expert_curated"
    review_status: ReviewStatus = "draft"
    version: str = "0.1"
    provenance: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_answer(self):
        valid = set(self.options)
        if self.question_type == "single_choice":
            if self.correct_answer not in valid:
                raise ValueError("single_choice requires correct_answer present in options")
        else:
            answers = set(self.correct_answers or [])
            if not answers or not answers <= valid:
                raise ValueError("multiple_select requires valid correct_answers")
        return self


class ModelConfig(BaseModel):
    name: str
    provider: Literal["ollama", "openai_compatible"]
    model: str
    base_url: str
    api_key_env: str | None = None
    api_key: SecretStr | None = Field(default=None, exclude=True, repr=False)
    temperature: float = 0.0
    timeout: int = 120
    context_window: int | None = None
    max_output_tokens: int | None = None
    thinking: bool | None = None
    structured_outputs: bool = False


class ItemResult(BaseModel):
    question_id: str
    model_name: str
    raw_response: str
    parsed_answers: list[str]
    score: float
    exact: bool
    error: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model_metadata: dict = Field(default_factory=dict)


class BenchmarkRun(BaseModel):
    benchmark_path: str
    started_at: str
    finished_at: str
    models: list[dict]
    questions: list[dict]
    results: list[ItemResult]

