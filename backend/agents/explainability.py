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
    execution = state.get("execution_result") or {}
    public_results = [
        result for result in execution.get("results", [])
        if not result.get("is_hidden", result.get("isHidden", False))
    ]
    payload = {
        "problem_title": state.get("problem", {}).get("title", ""),
        "language": state.get("submission", {}).get("language", ""),
        "overall_score": state.get("overall_score"),
        "public_execution_summary": {
            "compilation_success": execution.get("compile_status") == "success",
            "public_cases_passed": sum(
                str(result.get("status", "")).lower() == "accepted"
                for result in public_results
            ),
            "public_cases_total": len(public_results),
        },
        "complexity_details": state.get("complexity_details"),
        "style_details": state.get("style_details"),
        "source_code": state.get("submission", {}).get("source_code", "")
    }

    fallback = {
        "strengths": [],
        "weaknesses": [],
        "deductions": [],
        "improvement_steps": [
            "Review the correctness, complexity, and style evidence above, then revise only the issue it identifies."
        ],
        "mentor_feedback": "AI-generated feedback is temporarily unavailable. This submission was evaluated, but a specific explanation could not be generated.",
        "key_insight": "Use the execution and complexity evidence above to guide your next revision."
    }

    result = await invoke_agent(prompt, payload, ExplainabilityOutput, fallback)
    result["feedback_source"] = "fallback" if result is fallback else "ai"
    return {"feedback": result}
