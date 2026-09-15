from pydantic import BaseModel
from agents.base import load_prompt, invoke_agent


class RecommendationOutput(BaseModel):
    recommended_topics: list[dict]
    recommended_problems: list[dict]
    recommended_articles: list[dict]
    recommended_videos: list[dict]
    learning_path: list[str]
    estimated_improvement: str


async def recommendation_node(state):
    feedback = state.get("feedback") or {}
    fallback = {"recommended_topics": [], "recommended_problems": [], "recommended_articles": [], "recommended_videos": [],
                "learning_path": feedback.get("improvement_steps", []), "estimated_improvement": "Not estimated"}
    return {"recommendations": await invoke_agent(load_prompt("recommendation"),
        {"feedback": feedback, "problem": state.get("problem")}, RecommendationOutput, fallback)}
