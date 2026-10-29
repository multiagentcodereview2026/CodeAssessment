from pydantic import BaseModel
from typing import List, Dict, Any
import re
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


def _is_style_only_advice(text: str) -> bool:
    return any(word in text.lower() for word in (
        "comment", "naming", "readability", "maintainability", "rename",
    ))


def _source_identifiers(source_code: str) -> set[str]:
    """Return code-derived anchors for validating AI advice."""
    reserved = {
        "for", "while", "if", "else", "return", "int", "char", "bool",
        "string", "vector", "set", "map", "std", "using", "namespace",
        "main", "true", "false", "auto", "const", "void", "include",
    }
    return {
        word.lower()
        for word in re.findall(r"\b[A-Za-z_]\w*\b", source_code or "")
        if word.lower() not in reserved
    }


def _is_specific_ai_step(
    step: Any,
    *,
    source_code: str,
    complexity: Dict[str, Any],
    category: str,
) -> bool:
    """Require source, evidence, and an actual action for AI guidance."""
    text = " ".join(str(step or "").lower().split())
    if not text or len(text) < 28:
        return False
    generic_only = (
        "use a better structure", "optimize the loop", "keep needed state",
        "improve efficiency", "review the complexity", "make it faster",
    )
    if any(phrase in text for phrase in generic_only):
        return False
    identifiers = _source_identifiers(source_code)
    source_anchor = any(re.search(rf"\b{re.escape(identifier)}\b", text) for identifier in identifiers)
    structural_anchor = any(phrase in text for phrase in (
        "inner loop", "nested loop", "repeated scan", "repeated pass",
        "recompute", "rebuild", "full pass", "outer loop",
    ))
    observed_time = str(complexity.get("time_complexity") or "").lower()
    time_anchor = bool(observed_time and observed_time in text)
    complexity_terms = set(re.findall(r"o\s*\([^)]*\)", text))
    before_after_complexity = time_anchor and len(complexity_terms) >= 2
    category_anchor = bool(category and category.lower() in text)
    concrete_action = any(word in text for word in (
        "track", "maintain", "replace", "remove", "update", "advance",
        "extend", "store", "sliding", "greedy", "pointer", "window",
        "reach", "index", "bound", "queue", "stack", "map",
    ))
    return bool(
        concrete_action
        and (source_anchor or structural_anchor)
        and before_after_complexity
        and (time_anchor or category_anchor)
    )


def _style_finding_text(value: Any) -> str:
    """Extract the readable message from an analyzer style finding."""
    if isinstance(value, dict):
        return str(value.get("message") or value.get("reason") or value.get("detail") or "").strip()
    return str(value or "").strip()


def _source_complexity_feedback(source_code: str, complexity: Dict[str, Any]) -> tuple[List[str], List[str]]:
    """Describe a measured complexity gap using observable source structure.

    This is intentionally structural rather than problem-name based.  It
    prevents a correct-but-slow program from receiving empty advice such as
    "review the analysis" when the source itself exposes repeated loops.
    """
    source = str(source_code or "")
    time = str(complexity.get("time_complexity") or "").strip()
    classification = str(complexity.get("time_classification") or "").upper()
    time_score = complexity.get("time_score")
    try:
        has_time_gap = classification not in {"", "OPTIMAL"} or float(time_score) < 25
    except (TypeError, ValueError):
        has_time_gap = classification not in {"", "OPTIMAL"}
    if not time or not has_time_gap:
        return [], []

    loop_headers = re.findall(r"\b(for|while)\s*\(", source)
    if len(loop_headers) >= 2:
        sequence = " → ".join(loop_headers[:3])
        evidence = (
            f"Your code repeats work through {len(loop_headers)} loops ({sequence}). "
            f"The saved analysis measures this path as {time} time."
        )
        step = (
            "Find the inner loop that starts the same work again for each outer iteration. "
            "Keep only the state needed for the next step so the collection is not rebuilt or rescanned from scratch."
        )
        return [evidence], [step]
    if loop_headers:
        return [f"The submitted source has a loop-driven {time} path in the saved analysis."], [
            "Inspect the loop body for repeated collection work and replace only that bottleneck."
        ]
    return [f"The saved source analysis reports {time} time and a non-optimal time result."], [
        "Apply the recorded complexity suggestion to the operation identified by the analysis."
    ]


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
    revealed_case = execution.get("revealed_feedback_case") or {}
    complexity = state.get("complexity_details") or {}
    style = state.get("style_details") or {}
    source_code = str(submission.get("source_code") or "")

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
    elif revealed_case:
        status = str(revealed_case.get("status") or "failed").replace("_", " ").lower()
        case_input = str(revealed_case.get("input") or "").strip()
        expected = str(revealed_case.get("expected_output") or "").strip()
        actual = str(revealed_case.get("actual_output") or "").strip()
        detail = f"The revealed feedback case did not pass ({status})."
        if case_input or expected or actual:
            detail += f" Input: {case_input or '—'}; expected: {expected or '—'}; your output: {actual or '—'}."
        weaknesses.append(detail)
        steps.append("Use the revealed feedback case to trace the condition that produces the unexpected output, then rerun the examples.")
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
    structural_weaknesses, structural_steps = _source_complexity_feedback(source_code, complexity)
    weaknesses.extend(structural_weaknesses)
    steps.extend(structural_steps)
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
            style_findings.extend(_style_finding_text(value) for value in values if value)
    # Comments are optional documentation, not a grading priority. Keep the
    # feedback focused on concrete structure/readability evidence instead.
    style_findings = [finding for finding in style_findings if "comment" not in finding.lower()]
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
    revealed_case = execution.get("revealed_feedback_case") or None
    payload = {
        "problem_title": state.get("problem", {}).get("title", ""),
        "problem_statement": state.get("problem", {}).get("statement") or state.get("problem", {}).get("description", ""),
        "problem_constraints": state.get("problem", {}).get("constraints") or [],
        "algorithmic_tag": state.get("problem", {}).get("category") or "",
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
        "revealed_feedback_case": revealed_case,
        "complexity_details": state.get("complexity_details"),
        "style_details": state.get("style_details"),
        "source_code": sanitize_code_comments(state.get("submission", {}).get("source_code", ""))
    }

    fallback = build_evidence_feedback(state)

    result = await invoke_agent(
        prompt, payload, ExplainabilityOutput, fallback,
        capability="explainability",
    )
    used_fallback = result.get("analysis_source") != "groq"
    result = dict(result)
    # A failed execution is the student's first task.  Preserve precise,
    # deterministic evidence ahead of optional style advice even if an AI
    # provider returns a generic response.
    has_correctness_issue = bool(
        str(execution.get("compile_status") or "").lower() not in {"", "success"}
        or any(str(case.get("status") or "").lower() != "accepted" for case in public_results)
        or revealed_case
    )
    # Deterministic source/test/style evidence is always retained.  The AI can
    # add educational wording, but it may not replace a concrete observation
    # with generic praise or an ungrounded recommendation.
    category = str((state.get("problem") or {}).get("category") or "")
    ai_specific_steps = [
        step for step in result.get("improvement_steps", [])
        if _is_specific_ai_step(
            step,
            source_code=str(state.get("submission", {}).get("source_code") or ""),
            complexity=state.get("complexity_details") or {},
            category=category,
        )
    ]
    if has_correctness_issue or fallback["weaknesses"]:
        # Deterministic test/source/style evidence is the authority. The AI
        # may improve tone, but generic or unsupported advice must not alter
        # the actual improvement path.
        # A validated AI step is allowed to use its mentor-friendly wording.
        # If the response was generic, deterministic evidence stays in charge.
        if not ai_specific_steps:
            result["mentor_feedback"] = fallback["mentor_feedback"]
            result["key_insight"] = fallback["key_insight"]
        result["weaknesses"] = _unique([*fallback["weaknesses"], *result.get("weaknesses", [])])
        result["improvement_steps"] = (
            _unique(ai_specific_steps) if ai_specific_steps else fallback["improvement_steps"]
        )
    result["feedback_source"] = "fallback" if used_fallback else "ai"
    return {"feedback": result}
