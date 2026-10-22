from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from agents.base import load_prompt, invoke_agent
from agents.revision_verification import unverified_revision
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


class GuidedRevisionOutput(BaseModel):
    """A deliberately non-solution-oriented next learning step."""

    stage: str
    title: str
    next_goal: str
    guided_steps: List[str] = []
    algorithm_outline: List[str] = []
    starter_fragment: Optional[str] = ""
    change_summary: Optional[str] = ""
    improvement_explanation: Optional[str] = ""


def unavailable_revision(state: EvaluationState) -> Dict[str, Any]:
    """Never return a canned solution for a different problem when AI is down."""
    problem = state.get("problem") or {}
    submission = state.get("submission") or {}
    title = str(problem.get("title") or "this problem").strip()
    language = str(submission.get("language") or "the submitted language").strip()
    return {
        "improved_code": "",
        "changes": [],
        "change_summary": f"A task-specific code rewrite for {title} was not generated.",
        "improvement_explanation": (
            f"The revision service is unavailable, so no replacement {language} code is shown. "
            "Use the assessment feedback above; submit again when personalized code suggestions are available."
        ),
    }


def guided_revision_fallback(stage: str, state: EvaluationState) -> Dict[str, Any]:
    """Safe, useful guidance when the optional model is unavailable.

    This intentionally contains no replacement program.  A fallback must not
    become an accidental answer key.
    """
    title = str((state.get("problem") or {}).get("title") or "this problem")
    if stage == "NO_CHANGE":
        return {
            "stage": stage,
            "title": "No revision needed",
            "next_goal": "Your submitted approach already satisfies the available correctness, complexity, and style evidence.",
            "guided_steps": [],
            "algorithm_outline": [],
            "starter_fragment": "",
            "change_summary": "No meaningful code change is justified for this submission.",
            "improvement_explanation": "Keep this solution as a reference and apply the same reasoning to a new problem.",
        }
    return {
        "stage": stage,
        "title": f"Next improvement for {title}",
        "next_goal": "Make one focused change, submit it, and request the next learning step from that new attempt.",
        "guided_steps": [
            "Identify the smallest part of the current approach that prevents it from handling general input.",
            "Write the algorithm in your own code before requesting another revision step.",
        ],
        "algorithm_outline": [],
        "starter_fragment": "",
        "change_summary": "This guided mode intentionally withholds a complete replacement solution.",
        "improvement_explanation": "The next step is unlocked from a changed submission, not by repeatedly requesting the same answer.",
    }


async def guided_revision_node(state: EvaluationState, stage: str) -> Dict[str, Any]:
    """Generate one bounded coaching step rather than a solved program."""
    prompt = load_prompt("guided_revision")
    submission = state.get("submission") or {}
    problem = state.get("problem") or {}
    execution = state.get("execution_result") or {}
    public_results = [
        {
            "case": index + 1,
            "status": str(result.get("status") or "unknown"),
            "error": result.get("error_message") if not result.get("is_hidden", result.get("isHidden", False)) else None,
        }
        for index, result in enumerate(execution.get("results") or [])
        if not result.get("is_hidden", result.get("isHidden", False))
    ]
    payload = {
        "stage": stage,
        "problem": {
            "title": problem.get("title", ""),
            "statement": problem.get("statement") or problem.get("description") or "",
            "constraints": problem.get("constraints") or [],
        },
        "source_code": submission.get("source_code", ""),
        "language": submission.get("language", "cpp"),
        "public_execution_results": public_results,
        "feedback": state.get("feedback"),
        "complexity_details": state.get("complexity_details"),
        "style_details": state.get("style_details"),
    }
    result = await invoke_agent(
        prompt,
        payload,
        GuidedRevisionOutput,
        guided_revision_fallback(stage, state),
    )
    result = dict(result)
    result["revision_source"] = "ai" if result.get("analysis_source") == "groq" else "fallback"
    # Guided mode must never present source code.  The model may use prose and
    # pseudocode in its outline, but executable fragments make it too easy to
    # reconstruct the answer without the student attempting the next stage.
    result["improved_code"] = ""
    result["starter_fragment"] = ""
    result["verification"] = {
        "status": "no_change" if stage == "NO_CHANGE" else "guided_step",
        "verified": False,
        "message": (
            "No revision is recommended for this submission."
            if stage == "NO_CHANGE"
            else "This is one learning step, not a replacement solution. Submit a changed attempt to unlock the next step."
        ),
    }
    return {"improved_code": result}


async def revision_node(state: EvaluationState) -> Dict[str, Any]:
    prompt = load_prompt("revision")
    submission = state.get("submission") or {}
    problem = state.get("problem") or {}
    execution = state.get("execution_result") or {}
    # Only send public execution evidence to the revision model.
    public_results = [
        {
            "case": index + 1,
            "status": str(result.get("status") or "unknown"),
            "error": result.get("error_message") if not result.get("is_hidden", result.get("isHidden", False)) else None,
        }
        for index, result in enumerate(execution.get("results") or [])
        if not result.get("is_hidden", result.get("isHidden", False))
    ]
    payload = {
        "problem": {
            "title": problem.get("title", ""),
            "statement": problem.get("statement") or problem.get("description") or "",
            "constraints": problem.get("constraints") or [],
        },
        "source_code": submission.get("source_code", ""),
        "language": submission.get("language", "cpp"),
        "public_execution_results": public_results,
        "feedback": state.get("feedback"),
        "complexity_details": state.get("complexity_details"),
        "style_details": state.get("style_details"),
    }
    fallback = unavailable_revision(state)

    result = await invoke_agent(prompt, payload, RevisionOutput, fallback)
    used_fallback = result.get("analysis_source") != "groq"
    # Protect older prompts/model responses from the known unrelated Two Sum
    # template. A suggestion is only useful when it belongs to this task.
    task_context = " ".join((
        str(problem.get("title") or ""),
        str(problem.get("statement") or problem.get("description") or ""),
    )).lower()
    suggested = str(result.get("improved_code") or "")
    if "twosum(" in suggested.lower() and "twosum(" not in task_context and "two sum" not in task_context:
        result = fallback
        used_fallback = True

    result = dict(result)
    result["revision_source"] = "fallback" if used_fallback else "ai"
    result["verification"] = unverified_revision(
        "This generated draft has not been judged yet."
    )
    return {"improved_code": result}
