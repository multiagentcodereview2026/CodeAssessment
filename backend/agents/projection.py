from typing import Any, Dict
from workflow.state import EvaluationState


def _score(value: Any) -> float | None:
    try:
        return round(max(0.0, min(100.0, float(value))), 1)
    except (TypeError, ValueError):
        return None

async def score_projection_node(state: EvaluationState) -> Dict[str, Any]:
    """Calculate a conditional, evidence-based revision scenario.

    The suggested code has not yet been judged, so this is never a promise.
    It shows the score unlocked if correctness is fixed while the measured
    complexity and style components remain unchanged.
    """
    current_score = _score(state.get("overall_score")) or 0.0
    correctness = _score(state.get("correctness_score"))
    gate = (state.get("score_breakdown") or {}).get("correctness_gate") or {}
    raw_score = _score(gate.get("raw_score"))
    unavailable = {
        "available": False,
        "verified": False,
        "projected_score": None,
        "current_score": current_score,
        "expected_improvement": None,
        "assumptions": [],
        "message": "Submit revised code to the judge to receive a verified score.",
    }
    if correctness is None or raw_score is None:
        return {"projected_score": unavailable, "status": "complete"}
    if correctness >= 100.0:
        unavailable["message"] = "This submission already passed all evaluated cases; a new score requires a newly submitted revision."
        return {"projected_score": unavailable, "status": "complete"}

    expected_score = max(current_score, raw_score)
    result = {
        "available": True,
        "verified": False,
        "projection_basis": "correctness_fix_scenario",
        "projected_score": expected_score,
        "current_score": current_score,
        "expected_improvement": round(expected_score - current_score, 1),
        "assumptions": [
            "The revised code passes every evaluated test case.",
            "Its time complexity, space complexity, and style scores remain unchanged.",
        ],
        "message": "This is an expected score scenario, not a verified result. Submit the exact revised code to the judge to confirm it.",
    }
    return {
        "projected_score": result,
        "status": "complete"
    }
