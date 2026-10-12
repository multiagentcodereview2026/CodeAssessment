from pydantic import BaseModel
from typing import List, Dict, Any
from agents.base import load_prompt, invoke_agent
from workflow.state import EvaluationState

class TopicRec(BaseModel):
    topic: str
    reason: str
    priority: str

class ProblemRec(BaseModel):
    title: str
    platform: str
    difficulty: str
    reason: str

class RecommendationOutput(BaseModel):
    recommended_topics: List[TopicRec]
    recommended_problems: List[ProblemRec]
    recommended_articles: List[Dict[str, str]]
    recommended_videos: List[Dict[str, str]]
    learning_path: List[str]
    estimated_improvement: str

async def recommendation_node(state: EvaluationState) -> Dict[str, Any]:
    prompt = load_prompt("recommendation")
    payload = {
        "feedback": state.get("feedback"),
        "complexity_details": state.get("complexity_details"),
        "problem_title": state.get("problem", {}).get("title")
    }

    # Do not invent personalized practice when the LLM is unavailable. The
    # UI can truthfully present an empty recommendation state and retry later.
    fallback = {
        "recommended_topics": [], "recommended_problems": [],
        "recommended_articles": [], "recommended_videos": [],
        "learning_path": [], "estimated_improvement": "Unavailable until assessment evidence is available"
    }

    result = await invoke_agent(prompt, payload, RecommendationOutput, fallback)
    return {"recommendations": result}
