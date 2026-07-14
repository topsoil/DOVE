import json

from dove.answer_parser import parse_answer
from dove.benchmark_loader import load_benchmark
from dove.schemas import BenchmarkItem
from dove.scorer import score_answer


def test_example_benchmark_loads():
    items = load_benchmark("data/benchmarks/bioinformatics_v0_1.json")
    assert len(items) == 2
    assert {item.question_type for item in items} == {"single_choice", "multiple_select"}


def test_parse_json_and_plain_answer():
    assert parse_answer('{"answers": ["A", "C"]}', ["A", "B", "C"]) == ["A", "C"]
    assert parse_answer("Final answer: B", ["A", "B", "C"]) == ["B"]


def test_single_and_multiple_scoring():
    single = BenchmarkItem(id="s", domain="x", question_type="single_choice",
        question="?", options={"A": "a", "B": "b"}, correct_answer="B")
    assert score_answer(single, ["B"]) == (1.0, True)

    multiple = BenchmarkItem(id="m", domain="x", question_type="multiple_select",
        question="?", options={"A": "a", "B": "b", "C": "c"},
        correct_answers=["A", "C"])
    assert score_answer(multiple, ["A"]) == (0.5, False)
    assert score_answer(multiple, ["A", "B"]) == (0.0, False)

