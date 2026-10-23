from typing import Any, Dict
from scoring.rubric import complexity_dimension_percent, student_rubric_score
from workflow.state import EvaluationState


def _score(value: Any) -> float | None:
    try:
        return round(max(0.0, min(100.0, float(value))), 1)
    except (TypeError, ValueError):
        return None


def _weight(value: Any) -> float | None:
    """Read the effective correctness weight saved by the official rubric."""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if 0.0 < parsed <= 1.0 else None


def verified_revision_projection(
    *,
    current_score: Any,
    correctness_score: Any,
    complexity_details: Dict[str, Any] | None,
    style_score: Any,
) -> Dict[str, Any]:
    """Build an exact score scenario from a judge-assessed revision stage.

    The candidate code has already run through the same deterministic rubric
    components as a submission.  It is still a *projection* because the
    learner has not submitted that exact source as their own official attempt.
    """
    current = _score(current_score)
    projected, breakdown = student_rubric_score(
        correctness_score,
        complexity_details,
        style_score,
    )
    time = complexity_dimension_percent(complexity_details, "time")
    space = complexity_dimension_percent(complexity_details, "space")
    if current is None:
        return {
            "available": False,
            "verified": False,
            "projected_score": None,
            "current_score": None,
            "expected_improvement": None,
            "assumptions": [],
            "message": "The original score is unavailable, so this revision stage cannot be compared yet.",
        }

    delta = round(projected - current, 1)
    return {
        "available": True,
        "verified": True,
        "projection_basis": "verified_revision_stage",
        "projected_score": projected,
        "current_score": current,
        "expected_improvement": delta,
        "stage_components": {
            "correctness": _score(correctness_score),
            "time": _score(time),
            "space": _score(space),
            "style": _score(style_score),
        },
        "score_breakdown": breakdown,
        "assumptions": [
            "This exact guided-stage code was compiled and evaluated by the judge.",
            "Submit your own revision to receive an official saved score.",
        ],
        "message": (
            "This is a verified score projection for this one revision stage; "
            "it is not an official submission score."
        ),
    }


async def score_projection_node(state: EvaluationState) -> Dict[str, Any]:
    """Calculate a conditional, evidence-based revision scenario.

    The suggested code has not yet been judged, so this is never a promise.
    It recalculates the *official rubric formula* with correctness set to
    100%, while preserving the assessed time, space, and style components.
    It does not predict that a future revision will meet those assumptions.
    """
    current_score = _score(state.get("overall_score")) or 0.0
    correctness = _score(state.get("correctness_score"))
    score_breakdown = state.get("score_breakdown") or {}
    gate = score_breakdown.get("correctness_gate") or {}
    raw_score = _score(gate.get("raw_score"))
    correctness_weight = _weight(
        (score_breakdown.get("correctness") or {}).get("effective_weight")
    )
    unavailable = {
        "available": False,
        "verified": False,
        "projected_score": None,
        "current_score": current_score,
        "expected_improvement": None,
        "assumptions": [],
        "message": "Submit revised code to the judge to receive a verified score.",
    }
    revision = state.get("improved_code") or {}
    verification = revision.get("verification") if isinstance(revision, dict) else {}
    verification_status = str((verification or {}).get("status") or "")
    if correctness is None or raw_score is None or correctness_weight is None:
        unavailable["message"] = "A score scenario is unavailable because the saved rubric breakdown is incomplete."
        return {"projected_score": unavailable, "status": "complete"}
    if correctness >= 100.0:
        unavailable["message"] = "This submission already passed all evaluated cases; a new score requires a newly submitted revision."
        return {"projected_score": unavailable, "status": "complete"}

    if verification_status == "verification_failed":
        unavailable["message"] = "The displayed generated draft did not pass every evaluated case, so no score projection is shown for it."
        return {"projected_score": unavailable, "status": "complete"}

    # ``raw_score`` still includes the current partial correctness component.
    # Replacing that one component with 100% gives the only honest conditional
    # scenario; using raw_score alone would understate the result.
    expected_score = round(min(100.0, raw_score + (100.0 - correctness) * correctness_weight), 1)
    if expected_score <= current_score:
        unavailable["message"] = "Fixing correctness alone would not raise this saved score scenario. Submit a revision for a newly assessed score."
        return {"projected_score": unavailable, "status": "complete"}

    result = {
        "available": True,
        "verified": False,
        "projection_basis": "same_components_after_correctness_fix",
        "projected_score": expected_score,
        "current_score": current_score,
        "expected_improvement": round(expected_score - current_score, 1),
        "calculation": {
            "current_uncapped_score": raw_score,
            "current_correctness": correctness,
            "correctness_effective_weight": correctness_weight,
            "assumed_correctness": 100.0,
        },
        "assumptions": [
            "The revised code passes every evaluated test case.",
            "Its time complexity, space complexity, and style scores remain unchanged.",
        ],
        "message": "This conditional scenario applies the official rubric with correctness set to 100%. It is not a verified result; submit the exact revised code to the judge to confirm it.",
    }
    if verification_status == "verified_passed":
        result["revision_verification"] = "passed_all_evaluated_cases"
        result["message"] = "The displayed generated revision passed every evaluated case. Its final official score still requires a student submission, because complexity and style are assessed from the submitted code."
    return {
        "projected_score": result,
        "status": "complete"
    }
