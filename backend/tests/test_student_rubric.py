from agents.aggregation import aggregation_node
from scoring.rubric import student_rubric_score
import asyncio


def test_student_rubric_uses_20_30_30_20_weights():
    score, breakdown = student_rubric_score(
        80,
        {"time_score": 20, "time_score_max": 25, "space_score": 15, "space_score_max": 25},
        90,
    )
    assert score == 76.0
    assert breakdown["correctness"]["weight"] == 0.20
    assert breakdown["time"]["weight"] == 0.30
    assert breakdown["space"]["weight"] == 0.30
    assert breakdown["style"]["weight"] == 0.20


def test_similarity_cannot_change_a_student_score():
    base = {
        "correctness_score": 80,
        "complexity_details": {"time_score": 20, "time_score_max": 25, "space_score": 15, "space_score_max": 25},
        "style_score": 90,
    }
    low_risk = asyncio.run(aggregation_node({**base, "similarity_score": 0}))
    high_risk = asyncio.run(aggregation_node({**base, "similarity_score": 100}))
    assert low_risk["overall_score"] == high_risk["overall_score"] == 76.0
    assert "originality" not in low_risk["score_breakdown"]
