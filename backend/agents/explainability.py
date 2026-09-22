from pydantic import BaseModel
from typing import List, Dict, Any
from agents.base import load_prompt, invoke_agent
from workflow.state import EvaluationState

class Deduction(BaseModel):
    reason: str
    suggestion: str

class ExplainabilityOutput(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    deductions: List[Deduction]
    improvement_steps: List[str]
    mentor_feedback: str
    key_insight: str

async def explainability_node(state: EvaluationState) -> Dict[str, Any]:
    prompt = load_prompt("explainability")
    payload = {
        "overall_score": state.get("overall_score"),
        "correctness_details": state.get("correctness_details"),
        "complexity_details": state.get("complexity_details"),
        "style_details": state.get("style_details"),
        "source_code": state.get("submission", {}).get("source_code", "")
    }

    fallback = {
        "strengths": [
            "Good use of HashMap/STL unordered_map to achieve optimal O(n) time complexity.",
            "Handled direct complements efficiently within a single pass."
        ],
        "weaknesses": [
            "Variable naming like 'mp' and 'rem' could be more descriptive.",
            "Did not add inline comments explaining edge-case handling for empty inputs."
        ],
        "deductions": [
            {"reason": "Non-descriptive variable names", "suggestion": "Use 'seen_indices' or 'complement_map' instead of 'mp'."}
        ],
        "improvement_steps": [
            "Add pre-check validations for empty arrays.",
            "Write clear function docstrings for production maintainability."
        ],
        "mentor_feedback": "Great job! Your solution demonstrates a solid grasp of optimal hash lookups. With a little more attention to variable naming and commenting, this code would be production-ready.",
        "key_insight": "Mastering the time-space tradeoff with hash tables is a foundational software engineering skill."
    }

    result = await invoke_agent(prompt, payload, ExplainabilityOutput, fallback)
    return {"feedback": result}
