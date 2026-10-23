from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from agents.base import load_prompt, invoke_agent
from agents.revision_verification import unverified_revision
from workflow.state import EvaluationState


def _normalize_code_snippet(value: Any) -> str:
    """Keep model-produced teaching snippets valid source-code text.

    Natural-language models occasionally emit mathematical Unicode operators
    (for example ``≠``) inside otherwise valid C++/Java/Python snippets.
    Normalizing them here preserves the intended small diff without silently
    handing a learner uncompilable syntax.
    """
    text = str(value or "")
    return text.translate(str.maketrans({
        "≠": "!=" , "≤": "<=", "≥": ">=", "→": "->",
        "“": '"', "”": '"', "‘": "'", "’": "'",
    }))


def guided_future_plan(stage: str) -> list[str]:
    """Keep the visible learning path ordered even if a model suggests it out of order."""
    plans = {
        "OPTIMIZE_MANUAL_WORK": [
            "OPTIMIZE_DATA_STRUCTURE: after this smaller improvement is assessed, remove repeated whole-collection ordering with a structure suited to selecting the next two values.",
            "REFINEMENT: once the measured performance bottleneck is resolved, improve naming, formatting, and edge-case clarity.",
        ],
        "OPTIMIZE_LOCAL": [
            "OPTIMIZE_DATA_STRUCTURE: after this smaller improvement is assessed and shows a measured gain, consider a different structure or algorithm family for the remaining bottleneck.",
            "REFINEMENT: once performance is resolved, improve naming, formatting, and edge-case clarity.",
        ],
        "OPTIMIZE_DATA_STRUCTURE": [
            "REFINEMENT: after the new approach is assessed, improve readability and boundary handling without changing the algorithm again.",
        ],
    }
    return plans.get(stage, [])


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
    """One bounded coaching stage, never a replacement solution."""

    stage: str
    title: str
    next_goal: str
    guided_steps: List[str] = []
    algorithm_outline: List[str] = []
    improved_code: str = ""
    changes: Optional[List[LineChange]] = []
    future_plan: List[str] = []
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
    """Safe guidance when the optional model is unavailable."""
    title = str((state.get("problem") or {}).get("title") or "this problem")
    if stage == "NO_CHANGE":
        return {
            "stage": stage,
            "title": "No revision needed",
            "next_goal": "Your submitted approach already satisfies the available correctness, complexity, and style evidence.",
            "guided_steps": [],
            "algorithm_outline": [],
            "starter_fragment": "",
            "improved_code": "",
            "changes": [],
            "future_plan": [],
            "change_summary": "No meaningful code change is justified for this submission.",
            "improvement_explanation": "Keep this solution as a reference and apply the same reasoning to a new problem.",
        }
    stage_guidance = {
        "OPTIMIZE_MANUAL_WORK": {
            "title": "Remove repeated manual ordering",
            "next_goal": "Keep the current collection, but replace its repeated hand-written ordering work with one standard ordering operation per round.",
            "guided_steps": [
                "Identify the nested loops that only exist to order the current collection.",
                "Use one standard ordering operation for the collection at the start of each round.",
                "Keep the existing remove-two, compare, and reinsert behaviour unchanged in this stage.",
            ],
            "algorithm_outline": [
                "While more than one value remains, order the current collection once.",
                "Remove the two largest values using the ordering you created.",
                "Return the non-zero difference to the collection, then repeat.",
            ],
            "change_summary": "This removes the hand-written repeated ordering passes without changing the overall approach yet.",
            "improvement_explanation": "First make one local performance improvement. A later stage can replace repeated full ordering with a more suitable data structure if the new measurement still needs it.",
        },
        "OPTIMIZE_LOCAL": {
            "title": "Remove one repeated pass",
            "next_goal": "Find the repeated full-input pass identified by the assessment and remove it without changing the algorithm family.",
            "guided_steps": [
                "Locate the repeated scan or recomputation inside the outer loop.",
                "Retain only the state needed for the next iteration instead of rebuilding it.",
                "Submit this single local improvement before considering a new data structure.",
            ],
            "algorithm_outline": [
                "Keep the current approach and its correctness condition.",
                "Carry forward the result of the repeated work where possible.",
                "Perform only the update needed for the next iteration.",
            ],
            "change_summary": "This stage targets one unnecessary repeated operation, not a replacement solution.",
            "improvement_explanation": "A data-structure or algorithm change is intentionally deferred until this smaller improvement has been submitted and measured.",
        },
        "OPTIMIZE_DATA_STRUCTURE": {
            "title": "Choose a structure for the remaining bottleneck",
            "next_goal": "Replace the remaining expensive selection or lookup work with a structure that makes the required next value efficient to obtain.",
            "guided_steps": [
                "Name the operation that remains expensive after the local improvement.",
                "Choose a structure designed for that operation rather than repeatedly scanning or ordering every value.",
                "Re-check the existing edge cases after moving the state into the new structure.",
            ],
            "algorithm_outline": [
                "Initialize the structure from the input values.",
                "Repeatedly obtain the required next values through the structure's intended operation.",
                "Update or reinsert only the derived value required by the problem.",
            ],
            "change_summary": "The earlier local optimization has been measured; this stage can now address the remaining structural bottleneck.",
            "improvement_explanation": "After this implementation is assessed, the remaining work should be limited to correctness edges and readability.",
        },
    }.get(stage)
    if stage_guidance:
        return {
            "stage": stage,
            **stage_guidance,
            "starter_fragment": "",
            "improved_code": "",
            "changes": [],
            "future_plan": guided_future_plan(stage),
        }
    previous = state.get("previous_revision") or {}
    compared_stage = str(previous.get("stage") or "earlier submission").replace("_", " ").lower()
    return {
        "stage": stage,
        "title": f"Next improvement for {title}",
        "next_goal": (
            f"Compare this code with the {compared_stage} stage, keep the changes that work, "
            "and make one remaining evidence-backed improvement."
            if previous else
            "Make one focused change, submit it, and request the next learning step from that new attempt."
        ),
        "guided_steps": [
            "Keep the parts of the previous guided stage that are present in your current code.",
            "Use the current assessment evidence to change only the next remaining bottleneck.",
        ],
        "algorithm_outline": [],
        "starter_fragment": "",
        "improved_code": "",
        "changes": [],
        "future_plan": [
            "Submit your own implementation of this stage and review the new evidence.",
            "Use the next revision only for the remaining measured bottleneck.",
        ],
        "change_summary": "This guided mode intentionally withholds a complete replacement solution.",
        "improvement_explanation": "A later submission is compared with the previous guided stage so each revision advances the code instead of repeating the same advice.",
    }


async def guided_revision_node(state: EvaluationState, stage: str) -> Dict[str, Any]:
    """Generate one bounded learning stage rather than a final rewrite."""
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
        "previous_revision": state.get("previous_revision"),
    }
    result = await invoke_agent(
        prompt,
        payload,
        GuidedRevisionOutput,
        guided_revision_fallback(stage, state),
    )
    result = dict(result)
    result["revision_source"] = "ai" if result.get("analysis_source") == "groq" else "fallback"
    # Guided stages intentionally never expose implementation text. The useful
    # artifact is a conceptual next step and a later learning plan; this keeps
    # the student responsible for writing and understanding the change.
    result["improved_code"] = ""
    result["changes"] = []
    ordered_future_plan = guided_future_plan(stage)
    if ordered_future_plan:
        result["future_plan"] = ordered_future_plan
    result["starter_fragment"] = ""
    result["verification"] = {
        "status": "no_change" if stage == "NO_CHANGE" else "guided_step",
        "verified": False,
        "message": (
            "No revision is recommended for this submission."
            if stage == "NO_CHANGE"
            else "This is one scoped learning stage. Write the approach in your own code and submit it to unlock the next stage."
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
