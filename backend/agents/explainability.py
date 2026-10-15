from pydantic import BaseModel
from typing import List, Dict, Any
from agents.base import load_prompt, invoke_agent, sanitize_code_comments
from workflow.state import EvaluationState


def _unique(items: List[str], limit: int = 3) -> List[str]:
    seen = set()
    result = []
    for item in items:
        text = " ".join(str(item).split())
        if text and text.lower() not in seen:
            seen.add(text.lower())
            result.append(text)
        if len(result) >= limit:
            break
    return result


def build_evidence_feedback(state: EvaluationState) -> Dict[str, Any]:
    """Create per-submission feedback from observed evidence when AI is offline."""
    problem = state.get("problem") or {}
    submission = state.get("submission") or {}
    execution = state.get("execution_result") or {}
    title = str(problem.get("title") or "this problem")
    language = str(submission.get("language") or "your chosen language")
    results = execution.get("results") or []
    public_results = [
        result for result in results
        if not result.get("is_hidden", result.get("isHidden", False))
    ]
    passed = sum(str(result.get("status", "")).lower() == "accepted" for result in public_results)
    total = len(public_results)
    failed = [
        (index + 1, result)
        for index, result in enumerate(public_results)
        if str(result.get("status", "")).lower() != "accepted"
    ]
    compile_status = str(execution.get("compile_status") or "").lower()
    compile_failed = bool(compile_status) and compile_status != "success"
    complexity = state.get("complexity_details") or {}
    style = state.get("style_details") or {}

    strengths: List[str] = []
    weaknesses: List[str] = []
    steps: List[str] = []
    if total:
        strengths.append(f"Your {language} submission for {title} passed {passed} of {total} public examples.")
    if compile_failed:
        diagnostic = str(execution.get("compile_error") or execution.get("stderr") or "").strip()
        first_line = next((line.strip() for line in diagnostic.splitlines() if line.strip()), "")
        if first_line:
            first_line = first_line[:220]
            weaknesses.append(f"The submission did not compile. First compiler message: {first_line}")
        else:
            weaknesses.append("The submission did not compile, so execution feedback is not available yet.")
        steps.append("Fix the first compiler diagnostic, then run the public examples again.")
    elif failed:
        ordinal, failed_result = failed[0]
        status = str(failed_result.get("status") or "failed").replace("_", " ")
        weaknesses.append(f"Public test case {ordinal} did not pass ({status}).")
        steps.append(f"Review the logic exercised by public test case {ordinal}, then rerun the examples.")
    elif total:
        strengths.append("All displayed public examples passed for this submission.")

    time_complexity = complexity.get("time_complexity")
    space_complexity = complexity.get("space_complexity")
    if time_complexity or space_complexity:
        estimates = []
        if time_complexity:
            estimates.append(f"time {time_complexity}")
        if space_complexity:
            estimates.append(f"extra space {space_complexity}")
        strengths.append("The analysis estimates " + " and ".join(estimates) + ".")
    complexity_issue = str(complexity.get("optimization_suggestion") or "").strip()
    if complexity_issue and complexity_issue.lower() not in {"none", "n/a", "no optimization suggestion was available."}:
        weaknesses.append(complexity_issue)
        steps.append(complexity_issue)
    else:
        scoring_reason = str(complexity.get("scoring_reason") or "").strip()
        if scoring_reason and complexity.get("time_status") not in {None, "SCORED"}:
            weaknesses.append(scoring_reason)
            steps.append(scoring_reason)

    style_findings = []
    for key in ("naming_issues", "readability_issues", "modularity_issues", "maintainability_issues"):
        values = style.get(key) or []
        if isinstance(values, list):
            style_findings.extend(str(value) for value in values if value)
    for finding in _unique(style_findings, 1):
        weaknesses.append(finding)
        steps.append(finding)

    if not steps:
        steps.append(f"No specific failure was found in the saved evidence for {title}; keep this version and check the stated constraints before your next submission.")
    if not strengths:
        strengths.append(f"This feedback is based on the saved {title} assessment; no successful execution evidence was available.")

    mentor_feedback = f"For {title}, "
    if total:
        mentor_feedback += f"your {language} code passed {passed}/{total} public examples. "
    elif compile_failed:
        mentor_feedback += f"your {language} submission needs to compile before it can be assessed. "
    if weaknesses:
        mentor_feedback += "Start with this evidence-based issue: " + weaknesses[0]
    else:
        mentor_feedback += "the saved analysis found no specific issue to change, so avoid rewriting working code without a reason."

    return {
        "strengths": _unique(strengths),
        "weaknesses": _unique(weaknesses),
        "deductions": [],
        "improvement_steps": _unique(steps),
        "mentor_feedback": mentor_feedback,
        "key_insight": weaknesses[0] if weaknesses else f"The saved evidence for {title} does not identify a required code change.",
        "feedback_source": "fallback",
    }

class Deduction(BaseModel):
    reason: str
    suggestion: str

class ExplainabilityOutput(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    deductions: List[Deduction]
    improvement_steps: List[str]
    mentor_feedback: str
    key_insight: str

async def explainability_node(state: EvaluationState) -> Dict[str, Any]:
    prompt = load_prompt("explainability")
    execution = state.get("execution_result") or {}
    public_results = [
        result for result in (execution.get("results") or [])
        if not result.get("is_hidden", result.get("isHidden", False))
    ]
    public_case_evidence = [
        {
            "case": index + 1,
            "status": str(result.get("status") or "unknown"),
            "error": result.get("error_message"),
        }
        for index, result in enumerate(public_results)
    ]
    payload = {
        "problem_title": state.get("problem", {}).get("title", ""),
        "problem_statement": state.get("problem", {}).get("statement") or state.get("problem", {}).get("description", ""),
        "problem_constraints": state.get("problem", {}).get("constraints") or [],
        "language": state.get("submission", {}).get("language", ""),
        "correctness_score": state.get("correctness_score"),
        "overall_score": state.get("overall_score"),
        "public_execution_summary": {
            "compilation_success": str(execution.get("compile_status") or "").lower() == "success",
            "public_cases_passed": sum(
                str(result.get("status", "")).lower() == "accepted"
                for result in public_results
            ),
            "public_cases_total": len(public_results),
            "public_cases": public_case_evidence,
        },
        "complexity_details": state.get("complexity_details"),
        "style_details": state.get("style_details"),
        "source_code": sanitize_code_comments(state.get("submission", {}).get("source_code", ""))
    }

    fallback = build_evidence_feedback(state)

    result = await invoke_agent(prompt, payload, ExplainabilityOutput, fallback)
    used_fallback = result is fallback
    result = dict(result)
    result["feedback_source"] = "fallback" if used_fallback else "ai"
    return {"feedback": result}
