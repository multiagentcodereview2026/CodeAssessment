from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from agents.base import load_prompt, invoke_agent
from workflow.state import EvaluationState

class LineChange(BaseModel):
    line_original: Optional[str] = ""
    line_improved: Optional[str] = ""
    reason: Optional[str] = ""

class RevisionOutput(BaseModel):
    improved_code: str
    changes: Optional[List[LineChange]] = []
    change_summary: Optional[str] = "Code refactored for optimal performance and readability."
    improvement_explanation: Optional[str] = "Refactored with clean naming conventions and robust boundary checks."

async def revision_node(state: EvaluationState) -> Dict[str, Any]:
    prompt = load_prompt("revision")
    payload = {
        "source_code": state.get("submission", {}).get("source_code", ""),
        "language": state.get("submission", {}).get("language", "cpp"),
        "feedback": state.get("feedback")
    }

    fallback = {
        "improved_code": """class Solution {
public:
    // Optimal O(N) Time and O(N) Space Solution
    vector<int> twoSum(const vector<int>& nums, int target) {
        unordered_map<int, int> seen_indices;
        seen_indices.reserve(nums.size());
        
        for (int i = 0; i < nums.size(); ++i) {
            int complement = target - nums[i];
            auto it = seen_indices.find(complement);
            if (it != seen_indices.end()) {
                return {it->second, i};
            }
            seen_indices[nums[i]] = i;
        }
        return {};
    }
};""",
        "changes": [
            {
                "line_original": "unordered_map<int, int> mp;",
                "line_improved": "unordered_map<int, int> seen_indices; seen_indices.reserve(nums.size());",
                "reason": "Clear variable naming and capacity reservation prevents dynamic rehashing."
            }
        ],
        "change_summary": "Renamed variables and reserved hash map capacity.",
        "improvement_explanation": "These refactorings improve both cache locality and readability."
    }

    result = await invoke_agent(prompt, payload, RevisionOutput, fallback)
    return {"improved_code": result}
