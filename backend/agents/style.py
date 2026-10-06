from pydantic import BaseModel
from typing import List, Dict, Any
from analysis.style_ast_analyzer import analyze_style
from workflow.state import EvaluationState

class StyleOutput(BaseModel):
    style_score: float
    naming_issues: List[str]
    readability_issues: List[str]
    modularity_issues: List[str]
    positive_aspects: List[str]
    summary: str

async def style_node(state: EvaluationState) -> Dict[str, Any]:
    submission = state.get("submission", {})
    result = analyze_style(
        submission.get("source_code", ""),
        submission.get("language", "cpp"),
    )
    return {
        "style_score": result["style_score"],
        "style_details": result
    }
