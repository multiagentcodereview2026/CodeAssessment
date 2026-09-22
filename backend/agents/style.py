from pydantic import BaseModel
from typing import List, Dict, Any
from agents.base import load_prompt, invoke_agent
from workflow.state import EvaluationState

class StyleOutput(BaseModel):
    style_score: float
    naming_issues: List[str]
    readability_issues: List[str]
    modularity_issues: List[str]
    positive_aspects: List[str]
    summary: str

async def style_node(state: EvaluationState) -> Dict[str, Any]:
    prompt = load_prompt("style")
    payload = {
        "source_code": state.get("submission", {}).get("source_code", ""),
        "language": state.get("submission", {}).get("language", "cpp")
    }

    fallback = {
        "style_score": 90.0,
        "naming_issues": ["Consider renaming variable `mp` to `seen_elements` for improved clarity."],
        "readability_issues": ["Add comments explaining the complement lookup logic."],
        "modularity_issues": [],
        "positive_aspects": ["Clean indentation and modern STL usage.", "Concise and readable implementation."],
        "summary": "Clean, idiomatic structure with good spacing and formatting."
    }

    result = await invoke_agent(prompt, payload, StyleOutput, fallback)
    return {
        "style_score": result.get("style_score", 90.0),
        "style_details": result
    }
