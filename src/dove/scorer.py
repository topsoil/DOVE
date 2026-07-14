from __future__ import annotations

from .schemas import BenchmarkItem


def score_answer(item: BenchmarkItem, parsed_answers: list[str]) -> tuple[float, bool]:
    predicted = set(parsed_answers)
    gold = {item.correct_answer} if item.question_type == "single_choice" else set(item.correct_answers or [])
    exact = predicted == gold
    if item.question_type == "single_choice":
        return (1.0 if exact else 0.0), exact
    if exact:
        return 1.0, True
    true_positive = len(predicted & gold)
    false_positive = len(predicted - gold)
    return max(0.0, (true_positive - false_positive) / len(gold)), False

