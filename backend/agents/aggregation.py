from pydantic import BaseModel
from typing import Dict, Any
from agents.base import load_prompt, invoke_agent
from workflow.state import EvaluationState

class BreakdownItem(BaseModel):
    score: float
    weight: float
    weighted: float

class AggregationOutput(BaseModel):
    overall_score: float
    breakdown: Dict[str, BreakdownItem]
    confidence: float
    reasoning: str

async def aggregation_node(state: EvaluationState) -> Dict[str, Any]:
    # Keep observed zeroes (for example, a compile failure) intact.  Missing
    # evidence is represented separately instead of being turned into a score.
    correctness = state.get("correctness_score")
    complexity = state.get("complexity_score")
    style = state.get("style_score")
    similarity = state.get("similarity_score")

    scored_components = [
        ("correctness", correctness, 0.40),
        ("complexity", complexity, 0.20),
        ("style", style, 0.20),
        ("originality", None if similarity is None else max(0.0, 100.0 - similarity), 0.10),
        ("execution", 100.0 if state.get("execution_result", {}).get("compile_status") == "success" else 0.0, 0.10),
    ]
    available_weight = sum(weight for _, score, weight in scored_components if score is not None)
    if available_weight == 0:
        overall = 0.0
    else:
        overall = round(
            sum(score * weight for _, score, weight in scored_components if score is not None)
            / available_weight,
            1,
        )

    effective_weights = {
        name: (weight / available_weight if score is not None and available_weight else 0.0)
        for name, score, weight in scored_components
    }

    # The detailed agents may explain their score, but aggregation is numerical
    # policy and must remain deterministic.
    correctness = 0.0 if correctness is None else correctness
    complexity = 0.0 if complexity is None else complexity
    style = 0.0 if style is None else style
    similarity = 100.0 if similarity is None else similarity
    originality = max(0.0, 100.0 - similarity)
    execution = 100.0 if state.get("execution_result", {}).get("compile_status") == "success" else 0.0

    prompt = load_prompt("aggregation")
    payload = {
        "correctness": correctness,
        "complexity": complexity,
        "style": style,
        "originality": originality,
        "execution": execution
    }

    fallback = {
        "overall_score": overall,
        "breakdown": {
            "correctness": {"score": correctness, "weight": effective_weights["correctness"], "weighted": round(effective_weights["correctness"] * correctness, 1)},
            "complexity": {"score": complexity, "weight": effective_weights["complexity"], "weighted": round(effective_weights["complexity"] * complexity, 1)},
            "style": {"score": style, "weight": effective_weights["style"], "weighted": round(effective_weights["style"] * style, 1)},
            "originality": {"score": originality, "weight": effective_weights["originality"], "weighted": round(effective_weights["originality"] * originality, 1)},
            "execution": {"score": execution, "weight": effective_weights["execution"], "weighted": round(effective_weights["execution"] * execution, 1)}
        },
        "confidence": 0.94,
        "reasoning": f"Calculated composite score of {overall} from the available assessment evidence."
    }

    result = await invoke_agent(prompt, payload, AggregationOutput, fallback)
    return {
        "overall_score": overall,
        "score_breakdown": result.get("breakdown", fallback["breakdown"]),
        "confidence": result.get("confidence", 0.94)
    }
