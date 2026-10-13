from typing import Dict, Any
from workflow.state import EvaluationState
from scoring.rubric import STUDENT_RUBRIC_WEIGHTS, student_rubric_score

async def aggregation_node(state: EvaluationState) -> Dict[str, Any]:
    # Student marks are intentionally independent of similarity. Similarity is
    # retained as instructor-only evidence and scored in staff reporting.
    overall, breakdown = student_rubric_score(
        state.get("correctness_score"),
        state.get("complexity_details"),
        state.get("style_score"),
    )
    breakdown["rubric"] = {"weights": {name: int(weight * 100) for name, weight in STUDENT_RUBRIC_WEIGHTS.items()}}
    return {
        "overall_score": overall,
        "score_breakdown": breakdown,
        "confidence": 0.94,
    }
