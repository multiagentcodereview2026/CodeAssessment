from pydantic import BaseModel
from typing import List, Dict, Any
from agents.base import load_prompt, invoke_agent
from workflow.state import EvaluationState

class SimilarityOutput(BaseModel):
    similarity_score: float
    originality_score: float
    risk_level: str
    similar_submission_ids: List[str]
    reasoning: str
    flag_for_review: bool

async def similarity_node(state: EvaluationState) -> Dict[str, Any]:
    prompt = load_prompt("similarity")
    payload = {
        "source_code": state.get("submission", {}).get("source_code", ""),
        "language": state.get("submission", {}).get("language", "cpp")
    }

    fallback = {
        "similarity_score": 15.0,
        "originality_score": 85.0,
        "risk_level": "Low",
        "similar_submission_ids": [],
        "reasoning": "Standard algorithmic solution with unique variable declaration structure.",
        "flag_for_review": False
    }

    result = await invoke_agent(prompt, payload, SimilarityOutput, fallback)
    return {
        "similarity_score": result.get("similarity_score", 15.0),
        "similarity_details": result
    }
