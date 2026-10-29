from typing import Dict, Any
from workflow.state import EvaluationState
from scoring.rubric import student_rubric_score

async def aggregation_node(state: EvaluationState) -> Dict[str, Any]:
    # Student marks are intentionally independent of similarity. Similarity is
    # retained as instructor-only review evidence, never a grade component.
    overall, breakdown = student_rubric_score(
        state.get("correctness_score"),
        state.get("complexity_details"),
        state.get("style_score"),
        state.get("scoring_weights"),
    )
    return {
        "overall_score": overall,
        "score_breakdown": breakdown,
    }
