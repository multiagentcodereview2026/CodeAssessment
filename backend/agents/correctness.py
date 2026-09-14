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


def calculate_correctness_score(exec_res: Dict[str, Any]) -> float:
    """
    Calculate correctness deterministically from sandbox execution results.

    The LLM does NOT decide this score.
    """

    if exec_res.get("compile_status") != "success":
        return 0.0

    results = exec_res.get("results") or []

    if results:
        passed = sum(
            1
            for result in results
            if str(result.get("status", "")).lower() == "accepted"
        )

        total = len(results)

        if total == 0:
            return 0.0

        return round((passed / total) * 100, 2)

    # Fallback only if individual results are unavailable.
    passed = int(exec_res.get("passed_cases", 0) or 0)
    failed = int(exec_res.get("failed_cases", 0) or 0)
    total = int(exec_res.get("total_cases", passed + failed) or 0)

    if total <= 0:
        return 0.0

    return round((passed / total) * 100, 2)


def sanitize_execution_for_llm(exec_res: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prevent hidden test inputs/outputs from being exposed to the LLM.
    """

    safe_exec = dict(exec_res)

    safe_results = []

    for result in exec_res.get("results", []):
        safe_result = dict(result)

        if safe_result.get("is_hidden"):
            safe_result.pop("input", None)
            safe_result.pop("expected_output", None)
            safe_result.pop("actual_output", None)

            # Do not let detailed hidden-case errors leak test information.
            safe_result.pop("stderr", None)
            safe_result.pop("error_message", None)

        safe_results.append(safe_result)

    safe_exec["results"] = safe_results

    return safe_exec


async def correctness_node(state: EvaluationState) -> Dict[str, Any]:
    prompt = load_prompt("correctness")

    exec_res = state.get("execution_result") or {}

    correctness_score = calculate_correctness_score(exec_res)

    results = exec_res.get("results") or []

    if results:
        passed = sum(
            1
            for result in results
            if str(result.get("status", "")).lower() == "accepted"
        )
        total = len(results)
        failed = total - passed
    else:
        passed = int(exec_res.get("passed_cases", 0) or 0)
        failed = int(exec_res.get("failed_cases", 0) or 0)
        total = int(exec_res.get("total_cases", passed + failed) or 0)

    safe_exec_res = sanitize_execution_for_llm(exec_res)

    payload = {
        "problem": state.get("problem"),
        "execution_result": safe_exec_res,
        "source_code": state.get("submission", {}).get("source_code", "")
    }

    runtime_errors = []

    for result in exec_res.get("results", []):
        status = str(result.get("status", "")).lower()

        if status in {
            "runtime_error",
            "time_limit_exceeded",
            "system_error"
        }:
            message = result.get("error_message")

            if message and not result.get("is_hidden"):
                runtime_errors.append(str(message))

    fallback = {
        "correctness_score": correctness_score,
        "passed_cases": passed,
        "failed_cases": failed,
        "compilation_success": exec_res.get("compile_status") == "success",
        "runtime_errors": runtime_errors,
        "reasoning": (
            f"The sandbox passed {passed} of {total} test cases."
        ),
        "summary": (
            f"Your solution passed {passed}/{total} test cases."
            if total > 0
            else "No test-case results were available."
        )
    }

    result = await invoke_agent(
        prompt,
        payload,
        CorrectnessOutput,
        fallback
    )

    # IMPORTANT:
    # The LLM may explain correctness, but it cannot alter the score.
    result["correctness_score"] = correctness_score
    result["passed_cases"] = passed
    result["failed_cases"] = failed
    result["compilation_success"] = (
        exec_res.get("compile_status") == "success"
    )

    return {
        "correctness_score": correctness_score,
        "correctness_details": result
    }
