import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_openai_judged_interview import clamp, json_object

def test_json_object_accepts_prefixed_json():
    assert json_object('result: {"scientific_correctness": 0.75}') == {"scientific_correctness": 0.75}

def test_clamp_enforces_score_range():
    assert clamp(-2) == 0.0
    assert clamp(0.4) == 0.4
    assert clamp(9) == 1.0
