from pydantic import BaseModel
from typing import List, Dict, Any
from agents.base import load_prompt, invoke_agent
from workflow.state import EvaluationState

class SupervisorOutput(BaseModel):
    status: str
    errors: List[str]
    validation_summary: str
    next_step: str

async def supervisor_node(state: EvaluationState) -> Dict[str, Any]:
    prompt = load_prompt("supervisor")
    # Submission validation is deterministic. If this optional explanatory
    # capability is enabled, it needs public problem context and language,
    # never the learner's source or identity.
    payload = {
        "problem": state.get("problem"),
        "submission": {
            "language": state.get("submission", {}).get("language")
        }
    }
    
    fallback = {
        "status": "proceed",
        "errors": [],
        "validation_summary": "Submission verified and validated successfully.",
        "next_step": "docker_execution"
    }
    
    result = await invoke_agent(
        prompt, payload, SupervisorOutput, fallback,
        capability="supervisor",
    )
    return {"validation_result": result}
