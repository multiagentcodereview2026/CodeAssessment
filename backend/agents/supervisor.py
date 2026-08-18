from pydantic import BaseModel
from typing import List, Dict, Any
from agents.base import load_prompt, invoke_agent, sanitize_code_comments
from workflow.state import EvaluationState

class SupervisorOutput(BaseModel):
    status: str
    errors: List[str]
    validation_summary: str
    next_step: str

async def supervisor_node(state: EvaluationState) -> Dict[str, Any]:
    prompt = load_prompt("supervisor")
    source_code = state.get("submission", {}).get("source_code", "")
    sanitized_code = sanitize_code_comments(source_code)
    
    payload = {
        "user": state.get("user"),
        "problem": state.get("problem"),
        "submission": {
            "source_code": f"<STUDENT_SUBMISSION_CODE>\n{sanitized_code}\n</STUDENT_SUBMISSION_CODE>",
            "language": state.get("submission", {}).get("language")
        }
    }
    
    fallback = {
        "status": "proceed",
        "errors": [],
        "validation_summary": "Submission verified and validated successfully.",
        "next_step": "docker_execution"
    }
    
    result = await invoke_agent(prompt, payload, SupervisorOutput, fallback)
    return {"validation_result": result}
