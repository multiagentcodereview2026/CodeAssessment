from agents.aggregation import aggregation_node
from scoring.rubric import student_rubric_score
import asyncio


def test_student_rubric_uses_20_30_30_20_weights():
    score, breakdown = student_rubric_score(
        80,
        {"time_score": 20, "time_score_max": 25, "space_score": 15, "space_score_max": 25},
        90,
    )
    assert score == 60.8
    assert breakdown["correctness"]["weight"] == 0.20
    assert breakdown["time"]["weight"] == 0.30
    assert breakdown["space"]["weight"] == 0.30
    assert breakdown["style"]["weight"] == 0.20
    assert breakdown["correctness_gate"] == {
        "raw_score": 76.0,
        "correctness_factor": 0.8,
        "score_before_cap": 60.8,
        "score_cap": 79.0,
        "final_score": 60.8,
        "accepted": False,
    }


def test_non_accepted_solution_cannot_receive_an_excellent_score():
    score, breakdown = student_rubric_score(
        99,
        {"time_score": 25, "time_score_max": 25, "space_score": 25, "space_score_max": 25},
        100,
    )

    assert breakdown["correctness_gate"]["raw_score"] == 99.8
    assert breakdown["correctness_gate"]["score_before_cap"] == 98.8
    assert score == 79.0


def test_similarity_cannot_change_a_student_score():
    base = {
        "correctness_score": 80,
        "complexity_details": {"time_score": 20, "time_score_max": 25, "space_score": 15, "space_score_max": 25},
        "style_score": 90,
    }
    low_risk = asyncio.run(aggregation_node({**base, "similarity_score": 0}))
    high_risk = asyncio.run(aggregation_node({**base, "similarity_score": 100}))
    assert low_risk["overall_score"] == high_risk["overall_score"] == 60.8
    assert "originality" not in low_risk["score_breakdown"]
