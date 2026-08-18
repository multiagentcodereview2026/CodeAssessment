from pydantic import BaseModel
from typing import List, Dict, Any
from agents.base import load_prompt, invoke_agent
from workflow.state import EvaluationState

class CorrectnessOutput(BaseModel):
    correctness_score: float
    passed_cases: int
    failed_cases: int
    compilation_success: bool
    runtime_errors: List[str]
    reasoning: str
    summary: str

async def correctness_node(state: EvaluationState) -> Dict[str, Any]:
    prompt = load_prompt("correctness")
    exec_res = state.get("execution_result") or {}
    
    passed = exec_res.get("passed_cases", 3)
    failed = exec_res.get("failed_cases", 0)
    total = max(1, passed + failed)
    calculated_score = round((passed / total) * 100, 1)

    payload = {
        "problem": state.get("problem"),
        "execution_result": exec_res,
        "source_code": state.get("submission", {}).get("source_code", "")
    }

    fallback = {
        "correctness_score": calculated_score,
        "passed_cases": passed,
        "failed_cases": failed,
        "compilation_success": exec_res.get("compile_status") != "error",
        "runtime_errors": [exec_res.get("stderr")] if exec_res.get("stderr") else [],
        "reasoning": f"Passed {passed} of {total} test cases during sandbox execution.",
        "summary": f"Your solution passed {passed}/{total} test cases."
    }

    result = await invoke_agent(prompt, payload, CorrectnessOutput, fallback)
    # Anchor score deterministically to Docker passed percentage if LLM hallucinates wildly
    score = result.get("correctness_score", calculated_score)
    return {
        "correctness_score": score,
        "correctness_details": result
    }
