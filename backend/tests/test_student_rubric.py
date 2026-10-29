import asyncio
import math
import pytest
from agents.aggregation import aggregation_node
from scoring.rubric import DEFAULT_WEIGHT_PERCENT, instructor_rubric_score, student_rubric_score, validate_weights


def details(time=100, space=100):
    return {"time_score": time, "time_score_max": 100, "space_score": space, "space_score_max": 100}


def test_default_weighted_quality_and_continuous_correctness_ceiling():
    score, breakdown = student_rubric_score(80, details(80, 60), 90)
    assert score == 76
    assert breakdown["rubric"]["weights"] == DEFAULT_WEIGHT_PERCENT
    assert breakdown["correctness_gate"]["rule"] == "min(weighted_score, correctness)"
    for c in [0, 20, 44/61*100, 79, 80, 99, 100]:
        score, breakdown = student_rubric_score(c, details(), 100)
        assert score == round(min(.3*c+70, c), 1)
        assert breakdown["correctness_gate"]["accepted"] is (c == 100)


def test_custom_weights_and_staff_marks_use_identical_policy_without_similarity():
    weights = {"correctness": 0, "time": 70, "space": 20, "style": 10}
    expected = student_rubric_score(65, details(), 100, weights)
    assert expected[0] == 65
    assert instructor_rubric_score(65, details(), 100, similarity=99, weights=weights) == expected
    for similarity in [0, 100]:
        state = {"correctness_score": 65, "complexity_details": details(), "style_score": 100, "scoring_weights": weights, "similarity_score": similarity}
        assert asyncio.run(aggregation_node(state))["overall_score"] == 65


def test_unavailable_component_has_bounds_and_never_renormalizes():
    score, breakdown = student_rubric_score(100, {"space_score": 25}, 100)
    assert score is None
    assert breakdown["assessment"] == {"status": "incomplete", "missing_components": ["time"], "score_lower_bound": 65, "score_upper_bound": 100}
    assert breakdown["time"]["effective_weight"] == .35
    assert student_rubric_score(None, details(), 100)[0] is None
    assert student_rubric_score(0, {}, 100)[0] == 0
    assert student_rubric_score(100, {}, 100, {"correctness": 90, "time": 0, "space": 0, "style": 10})[0] == 100


@pytest.mark.parametrize("weights", [{}, {"correctness": 30, "time": 35, "space": 25, "style": 20}, {"correctness": math.nan, "time": 35, "space": 25, "style": 10}, {"correctness": -1, "time": 66, "space": 25, "style": 10}])
def test_invalid_weights_rejected(weights):
    with pytest.raises(ValueError):
        validate_weights(weights)


def test_monotonicity_bounds_and_determinism():
    for c in range(0, 101, 5):
        previous = -1
        for t in range(0, 101, 5):
            result = student_rubric_score(c, details(t, 65), 80)
            assert result == student_rubric_score(c, details(t, 65), 80)
            assert 0 <= result[0] <= c
            assert result[0] >= previous
            previous = result[0]
