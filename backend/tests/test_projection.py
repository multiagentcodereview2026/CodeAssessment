import asyncio

from agents.projection import score_projection_node


def test_projection_is_a_transparent_correctness_fix_scenario():
    result = asyncio.run(score_projection_node({
        "overall_score": 66.5,
        "correctness_score": 72.13,
        "score_breakdown": {"correctness_gate": {"raw_score": 92.2}},
    }))["projected_score"]

    assert result["available"] is True
    assert result["verified"] is False
    assert result["projected_score"] == 92.2
    assert result["expected_improvement"] == 25.7


def test_projection_is_not_shown_as_a_gain_for_an_accepted_submission():
    result = asyncio.run(score_projection_node({
        "overall_score": 92.2,
        "correctness_score": 100,
        "score_breakdown": {"correctness_gate": {"raw_score": 92.2}},
    }))["projected_score"]

    assert result["available"] is False
    assert result["projected_score"] is None


def test_failed_generated_draft_does_not_receive_a_score_projection():
    result = asyncio.run(score_projection_node({
        "overall_score": 66.5,
        "correctness_score": 72.13,
        "score_breakdown": {"correctness_gate": {"raw_score": 92.2}},
        "improved_code": {"verification": {"status": "verification_failed"}},
    }))["projected_score"]

    assert result["available"] is False
    assert "did not pass" in result["message"]
