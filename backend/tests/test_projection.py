import asyncio

from agents.projection import score_projection_node, verified_revision_projection
from schemas import SubmissionDetails
import pytest


def test_projection_is_a_transparent_correctness_fix_scenario():
    result = asyncio.run(score_projection_node({
        "overall_score": 66.5,
        "correctness_score": 72.13,
        "score_breakdown": {
            "correctness": {"effective_weight": 0.20},
            "correctness_gate": {"raw_score": 92.2},
        },
    }))["projected_score"]

    assert result["available"] is True
    assert result["verified"] is False
    # 92.2 is the current uncapped score and still includes 72.13% correctness.
    # The scenario re-runs the rubric with correctness at 100%: +5.6 points.
    assert result["projected_score"] == 97.8
    assert result["expected_improvement"] == 31.3
    assert result["projection_basis"] == "same_components_after_correctness_fix"


def test_projection_is_not_shown_as_a_gain_for_an_accepted_submission():
    result = asyncio.run(score_projection_node({
        "overall_score": 92.2,
        "correctness_score": 100,
        "score_breakdown": {
            "correctness": {"effective_weight": 0.20},
            "correctness_gate": {"raw_score": 92.2},
        },
    }))["projected_score"]

    assert result["available"] is False
    assert result["projected_score"] is None


def test_failed_generated_draft_does_not_receive_a_score_projection():
    result = asyncio.run(score_projection_node({
        "overall_score": 66.5,
        "correctness_score": 72.13,
        "score_breakdown": {
            "correctness": {"effective_weight": 0.20},
            "correctness_gate": {"raw_score": 92.2},
        },
        "improved_code": {"verification": {"status": "verification_failed"}},
    }))["projected_score"]

    assert result["available"] is False
    assert "did not pass" in result["message"]


def test_projection_requires_the_saved_effective_rubric_weight():
    result = asyncio.run(score_projection_node({
        "overall_score": 45.0,
        "correctness_score": 0,
        "score_breakdown": {"correctness_gate": {"raw_score": 80.0}},
    }))["projected_score"]

    assert result["available"] is False
    assert "rubric breakdown is incomplete" in result["message"]


def test_verified_revision_stage_projection_uses_the_actual_stage_components():
    result = verified_revision_projection(
        current_score=75.0,
        correctness_score=100.0,
        complexity_details={
            "time_score": 20.0,
            "time_score_max": 25.0,
            "space_score": 25.0,
            "space_score_max": 25.0,
        },
        style_score=75.0,
    )

    # Current shared rubric: 30 correctness + 28 time + 25 space + 7.5 style.
    assert result["available"] is True
    assert result["verified"] is True
    assert result["projection_basis"] == "verified_revision_stage"
    assert result["projected_score"] == 90.5
    assert result["expected_improvement"] == 15.5
    assert result["stage_components"] == {
        "correctness": 100.0,
        "time": 80.0,
        "space": 100.0,
        "style": 75.0,
    }


def test_verified_projection_is_hidden_when_the_stage_does_not_improve_score():
    result = verified_revision_projection(
        current_score=100.0,
        correctness_score=100.0,
        complexity_details={
            "time_score": 25.0, "time_score_max": 25.0,
            "space_score": 25.0, "space_score_max": 25.0,
        },
        style_score=100.0,
    )

    assert result["available"] is False
    assert result["projected_score"] is None


def test_private_projection_data_is_not_in_the_student_schema():
    assert "private_projection" not in SubmissionDetails.model_fields


@pytest.mark.parametrize("current,complexity", [(75, {}), (None, {"time_score": 25, "space_score": 25}), (float("nan"), {"time_score": 25, "space_score": 25})])
def test_incomplete_or_nonfinite_assessment_has_no_promised_gain(current, complexity):
    result = verified_revision_projection(current_score=current, correctness_score=100, complexity_details=complexity, style_score=100)
    assert result["available"] is False
    assert result["projected_score"] is None
    assert result["expected_improvement"] is None


def test_candidate_projection_uses_custom_saved_weights():
    result = verified_revision_projection(current_score=75, correctness_score=100,
        complexity_details={"time_score": 20, "space_score": 25}, style_score=75,
        scoring_weights={"correctness": 20, "time": 50, "space": 20, "style": 10})
    assert result["projected_score"] == 87.5
    assert result["expected_improvement"] == 12.5
    assert "not guaranteed" in result["message"]
