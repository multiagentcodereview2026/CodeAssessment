from agents.aggregation import aggregation_node
from scoring.rubric import instructor_rubric_score, student_rubric_score
import asyncio
import pytest


def test_student_rubric_uses_declared_20_30_30_20_weights_without_double_counting():
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
    assert breakdown["correctness_gate"] == {
        "raw_score": 76.0,
        "score_before_cap": 76.0,
        "score_cap": 79.0,
        "final_score": 76.0,
        "accepted": False,
    }


def test_non_accepted_solution_cannot_receive_an_excellent_score():
    score, breakdown = student_rubric_score(
        99,
        {"time_score": 25, "time_score_max": 25, "space_score": 25, "space_score_max": 25},
        100,
    )

    assert breakdown["correctness_gate"]["raw_score"] == 99.8
    assert breakdown["correctness_gate"]["score_before_cap"] == 99.8
    assert score == 79.0


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


def test_missing_correctness_is_reported_as_unknown_and_available_weights_renormalize():
    score, breakdown = student_rubric_score(
        None,
        {"time_score": 20, "time_score_max": 25, "space_score": 25, "space_score_max": 25},
        100,
    )

    assert score == 92.5
    assert breakdown["correctness"]["score"] is None
    assert breakdown["correctness"]["effective_weight"] == 0.0
    assert breakdown["time"]["effective_weight"] == pytest.approx(0.375)
    assert breakdown["space"]["effective_weight"] == pytest.approx(0.375)
    assert breakdown["style"]["effective_weight"] == pytest.approx(0.25)
    assert breakdown["correctness_gate"]["accepted"] is None
    assert breakdown["correctness_gate"]["score_cap"] is None


def test_fully_accepted_solution_has_no_nonaccepted_cap():
    score, breakdown = student_rubric_score(
        100,
        {"time_score": 25, "time_score_max": 25, "space_score": 25, "space_score_max": 25},
        100,
    )

    assert score == 100.0
    assert breakdown["correctness_gate"]["accepted"] is True
    assert breakdown["correctness_gate"]["score_cap"] is None


def test_instructor_review_uses_separate_weights_and_similarity_as_originality():
    score, breakdown = instructor_rubric_score(
        80,
        {"time_score": 20, "time_score_max": 25, "space_score": 15, "space_score_max": 25},
        90,
        20,
    )

    assert score == 77.0
    assert breakdown["correctness"]["weight"] == 0.20
    assert breakdown["time"]["weight"] == 0.25
    assert breakdown["space"]["weight"] == 0.25
    assert breakdown["style"]["weight"] == 0.20
    assert breakdown["originality"]["weight"] == 0.10
    assert breakdown["originality"]["score"] == 80.0


def test_invalid_scores_are_clamped_and_missing_complexity_is_renormalized():
    score, breakdown = student_rubric_score(
        120,
        {"time_score": "invalid", "space_score": 20, "space_score_max": 25},
        -10,
    )

    assert score == 62.9
    assert breakdown["correctness"]["score"] == 100.0
    assert breakdown["time"]["score"] is None
    assert breakdown["space"]["score"] == 80.0
    assert breakdown["style"]["score"] == 0.0
