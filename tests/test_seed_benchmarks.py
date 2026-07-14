from collections import Counter

from dove.benchmark_loader import load_benchmark


def test_seed_benchmarks_have_expected_size_and_valid_gold():
    bio = load_benchmark("data/benchmarks/bioinformatics_best_practices_100.json")
    disease = load_benchmark("data/benchmarks/disease_genetics_100.json")
    assert len(bio) == 100
    assert len(disease) == 100
    assert len({item.id for item in bio + disease}) == 200
    assert sum(item.question_type == "multiple_select" for item in bio) == 10
    assert all(len(item.options) == 4 for item in bio + disease)
    assert all(item.source.startswith("https://") for item in bio + disease)
    assert {item.review_status for item in bio + disease} == {"llm_generated"}


def test_seed_answer_positions_are_balanced():
    bio = load_benchmark("data/benchmarks/bioinformatics_best_practices_100.json")
    disease = load_benchmark("data/benchmarks/disease_genetics_100.json")
    bio_positions = Counter(
        item.correct_answer for item in bio if item.question_type == "single_choice")
    disease_positions = Counter(item.correct_answer for item in disease)
    assert max(bio_positions.values()) - min(bio_positions.values()) <= 1
    assert disease_positions == Counter({"A": 25, "B": 25, "C": 25, "D": 25})


def test_seed_questions_are_unique():
    bio = load_benchmark("data/benchmarks/bioinformatics_best_practices_100.json")
    disease = load_benchmark("data/benchmarks/disease_genetics_100.json")
    questions = [item.question for item in bio + disease]
    assert len(questions) == len(set(questions))

