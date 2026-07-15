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



def test_dimi_pilot_has_valid_provenance_and_balanced_answers():
    dimi = load_benchmark("data/benchmarks/dimi_lab_60.json")
    assert len(dimi) == 60
    assert len({item.id for item in dimi}) == 60
    assert Counter(item.correct_answer for item in dimi) == Counter(
        {"A": 15, "B": 15, "C": 15, "D": 15}
    )
    assert {item.review_status for item in dimi} == {"corpus_generated"}
    assert all(item.provenance.get("chunk_ids") for item in dimi)
    assert {item.subdomain for item in dimi} == {
        "PPAR gene prioritization",
        "Serous endometrial cancer therapy",
    }


def test_gyn_surgical_note_extraction_benchmark_is_synthetic_and_complete():
    gyn = load_benchmark("data/benchmarks/gyn_surgical_note_extraction_100.json")
    assert len(gyn) == 100
    assert len({item.id for item in gyn}) == 100
    assert len({item.question for item in gyn}) == 100
    assert Counter(item.subdomain for item in gyn) == Counter({
        "Gynecologic surgical involvement": 12,
        "Laparoscopic approach": 12,
        "Extensive cytoreduction": 11,
        "Surgery aborted early": 11,
        "Residual disease": 12,
        "Disease burden": 11,
        "Estimated blood loss": 11,
        "Hemostasis": 10,
        "Wound classification": 10,
    })
    assert {item.review_status for item in gyn} == {"llm_generated"}
    assert all(item.question.startswith("Synthetic operative-note excerpt:") for item in gyn)
    assert all(item.provenance.get("synthetic") is True for item in gyn)
    assert all(item.provenance.get("contains_patient_data") is False for item in gyn)
    assert all(item.provenance.get("human_review_required") is True for item in gyn)
    assert all(item.source == "prompts/gyn_surgical_note_feature_extraction.md" for item in gyn)


def test_gyn_surgical_note_options_follow_extraction_specification():
    gyn = load_benchmark("data/benchmarks/gyn_surgical_note_extraction_100.json")
    allowed = {
        "Gynecologic surgical involvement": {"yes", "no", "unsure"},
        "Laparoscopic approach": {"yes", "no", "unsure"},
        "Extensive cytoreduction": {"yes", "no", "unsure"},
        "Surgery aborted early": {"yes", "no", "unsure"},
        "Residual disease": {"R0", "R0.5", "R1", "R2", "unspecified", "not_mentioned"},
        "Disease burden": {"pelvic_disease", "lower_abdominal_disease", "upper_abdominal_disease", "miliary_disease", "not_mentioned"},
        "Hemostasis": {"yes", "no", "not_mentioned"},
        "Wound classification": {"ClassI", "ClassII", "ClassIII", "ClassIV", "not_mentioned"},
    }
    for item in gyn:
        values = set(item.options.values())
        if item.subdomain == "Estimated blood loss":
            assert len(values) == 4
            assert all(value == "-1" or int(value) >= 0 for value in values)
        else:
            assert values == allowed[item.subdomain]
