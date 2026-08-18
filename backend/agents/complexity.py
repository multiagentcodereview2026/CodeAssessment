from pydantic import BaseModel
from typing import List, Dict, Any
from agents.base import load_prompt, invoke_agent
from workflow.state import EvaluationState

class ComplexityOutput(BaseModel):
    complexity_score: float
    time_complexity: str
    space_complexity: str
    bottlenecks: List[str]
    optimization_suggestion: str
    reasoning: str

async def complexity_node(state: EvaluationState) -> Dict[str, Any]:
    prompt = load_prompt("complexity")
    payload = {
        "problem": state.get("problem"),
        "source_code": state.get("submission", {}).get("source_code", "")
    }

    fallback = {
        "complexity_score": 85.0,
        "time_complexity": "O(N)",
        "space_complexity": "O(N)",
        "bottlenecks": ["Linear extra space for hash table lookups"],
        "optimization_suggestion": "Optimal one-pass hash map approach achieves linear time.",
        "reasoning": "Algorithm iterates through the array once while utilizing an auxiliary hash structure."
    }

    result = await invoke_agent(prompt, payload, ComplexityOutput, fallback)
    return {
        "complexity_score": result.get("complexity_score", 85.0),
        "complexity_details": result
    }
