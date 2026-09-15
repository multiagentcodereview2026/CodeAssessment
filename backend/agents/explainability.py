from pydantic import BaseModel
from agents.base import load_prompt, invoke_agent


class Deduction(BaseModel):
    reason: str
    suggestion: str


class ExplainabilityOutput(BaseModel):
    strengths: list[str]
    weaknesses: list[str]
    deductions: list[Deduction]
    improvement_steps: list[str]
    mentor_feedback: str
    key_insight: str


async def explainability_node(state):
    execution = state.get("execution_result") or {}
    passed, total = execution.get("passed_cases", 0), execution.get("total_cases", 0)
    compiled = execution.get("compile_status") == "success"
    summary = f"{passed} of {total} tests passed." if compiled else "Compilation failed; no runnable program was produced."
    steps = (["Review the compiler diagnostic, fix the reported error and run again."] if not compiled else
             ["Inspect the first failing public example and compare the expected output with your output.",
              "Check boundary inputs and run the full test suite after revising."] if passed < total else
             ["All supplied tests passed. Review the stated complexity constraints and document your approach."])
    fallback = {
        "strengths": [summary] if total and passed == total else [],
        "weaknesses": [summary] if not compiled or passed < total else [],
        "deductions": [], "improvement_steps": steps,
        "mentor_feedback": summary + " AI feedback is unavailable; this report uses observed execution evidence only.",
        "key_insight": "An accepted result verifies the supplied tests, not every possible input.",
    }
    payload = {key: state.get(key) for key in ("problem", "submission", "correctness_details", "complexity_details", "style_details")}
    payload["execution_result"] = execution
    return {"feedback": await invoke_agent(load_prompt("explainability"), payload, ExplainabilityOutput, fallback)}
