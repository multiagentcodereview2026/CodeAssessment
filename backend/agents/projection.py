from pydantic import BaseModel
from typing import Dict, Any
from agents.base import load_prompt, invoke_agent
from workflow.state import EvaluationState

class ScoreProjectionOutput(BaseModel):
    projected_score: float
    current_score: float
    confidence: float
    expected_improvement: float
    improvement_breakdown: Dict[str, float]
    timeline: str
    motivational_message: str

async def score_projection_node(state: EvaluationState) -> Dict[str, Any]:
    prompt = load_prompt("projection")
    current_score = state.get("overall_score")
    if current_score is None:
        current_score = 0.0

    payload = {
        "current_score": current_score,
        "correctness_score": state.get("correctness_score"),
        "complexity_score": state.get("complexity_score"),
        "style_score": state.get("style_score")
    }

    fallback = {
        # An invented fixed gain is misleading. Hide the projection unless it
        # was actually produced from this submission's evidence.
        "projected_score": None,
        "current_score": current_score,
        "confidence": 0.0,
        "expected_improvement": None,
        "improvement_breakdown": {},
        "timeline": "Unavailable",
        "motivational_message": "A personalized score projection is unavailable for this assessment."
    }

    result = await invoke_agent(prompt, payload, ScoreProjectionOutput, fallback)
    used_fallback = result is fallback
    result = dict(result)
    result["available"] = not used_fallback
    return {
        "projected_score": result,
        "status": "complete"
    }
