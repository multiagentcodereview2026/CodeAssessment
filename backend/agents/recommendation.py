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

    fallback = {
        "recommended_topics": [
            {"topic": "Hash Map Internals", "reason": "Deepen understanding of hash collisions and load factors.", "priority": "high"},
            {"topic": "Two Pointer Technique", "reason": "Alternative O(1) space approach on sorted data.", "priority": "medium"},
            {"topic": "Array Slicing & Boundary Checks", "reason": "Prevent buffer and index errors.", "priority": "low"}
        ],
        "recommended_problems": [
            {"title": "4Sum", "platform": "LeetCode", "difficulty": "medium", "reason": "Generalize the complement lookup pattern."},
            {"title": "Subarray Sum Equals K", "platform": "LeetCode", "difficulty": "medium", "reason": "Prefix sum + Hash map synergy."},
            {"title": "Complement of Base 10 Integer", "platform": "LeetCode", "difficulty": "easy", "reason": "Bitwise logic practice."}
        ],
        "recommended_articles": [
            {"title": "Hash Table Performance & Collision Resolution", "url": "https://geeksforgeeks.org/hashing-data-structure/", "reason": "Understand space/time tradeoffs."}
        ],
        "recommended_videos": [
            {"title": "Two Sum Explained - NeetCode", "channel": "NeetCode", "reason": "Visual comparison between O(N^2) and O(N)."}
        ],
        "learning_path": [
            "Review Hash Map memory layout and worst-case complexities.",
            "Solve 3 medium-level hash table problems.",
            "Implement a custom hash map from scratch."
        ],
        "estimated_improvement": "+7 to +12 points on next submission"
    }

    result = await invoke_agent(prompt, payload, RecommendationOutput, fallback)
    return {"recommendations": result}
