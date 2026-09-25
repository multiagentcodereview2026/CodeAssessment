"""Complexity analysis agent and private deterministic scoring bridge."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import re

from pydantic import BaseModel, Field

from agents.base import load_prompt, invoke_agent, sanitize_code_comments
from scoring.complexity import (
    normalize_complexity,
    private_time_complexity_breakdown,
    private_space_complexity_breakdown,
    space_complexity_assessment,
    time_complexity_assessment,
)
from workflow.state import EvaluationState


class ComplexityOutput(BaseModel):
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    bottlenecks: List[str] = Field(default_factory=list)
    optimization_suggestion: str = "No optimization suggestion was available."
    reasoning: str = "No complexity analysis was available."


def public_problem_context(problem: Dict[str, Any]) -> Dict[str, Any]:
    """Select the problem data that may safely be sent to the AI service."""
    constraints = problem.get("constraints") or []
    if isinstance(constraints, tuple):
        constraints = list(constraints)

    return {
        "title": problem.get("title", ""),
        "statement": problem.get("statement") or problem.get("description") or "",
        "constraints": constraints,
        "category": problem.get("category", ""),
        "difficulty": problem.get("difficulty", ""),
    }


def unavailable_analysis(reason: str) -> Dict[str, Any]:
    return {
        "time_complexity": None,
        "space_complexity": None,
        "bottlenecks": ["Complexity analysis was unavailable."],
        "optimization_suggestion": "Retry the assessment to obtain algorithmic complexity analysis.",
        "reasoning": reason,
    }


def infer_static_complexity(source_code: str) -> Dict[str, Any]:
    """Conservative local fallback for common, recognizable code shapes.

    This is intentionally modest: it provides useful results during model
    outages and returns review-required values for patterns it cannot justify.
    """
    code = source_code.lower()
    has_loop = bool(re.search(r"\b(for|while)\s*\(", code))
    has_binary_search = (
        has_loop and "mid" in code and
        ("left" in code or "low" in code) and
        ("right" in code or "high" in code)
    )
    has_sort = bool(re.search(r"\b(sort|stable_sort)\s*\(", code))
    nested_loop = bool(re.search(
        r"(?:for|while)[^\n]{0,180}\n(?:\s|\{)*[^\n]*(?:for|while)\s*\(", code
    ))

    if has_binary_search:
        time_complexity = "O(log n)"
    elif has_sort:
        time_complexity = "O(n log n)"
    elif nested_loop:
        time_complexity = "O(n^2)"
    elif has_loop:
        time_complexity = "O(n)"
    else:
        time_complexity = None

    allocates_linear_storage = bool(re.search(
        r"\b(vector|unordered_map|unordered_set|map|set|array)\b|\.push_back\s*\(",
        code,
    ))
    space_complexity = "O(n)" if allocates_linear_storage else ("O(1)" if time_complexity else None)
    return {
        "time_complexity": time_complexity,
        "space_complexity": space_complexity,
        "bottlenecks": ["Local static fallback used because the complexity model was unavailable."],
        "optimization_suggestion": "Verify the inferred complexity during review." if time_complexity else "Manual complexity review is required.",
        "reasoning": "Conservative local loop, sorting, search, and allocation pattern analysis.",
    }


async def analyze_student_complexity(
    problem: Dict[str, Any], source_code: str, language: str
) -> Dict[str, Any]:
    """Ask Groq to classify *student* code without any private benchmark.

    This function is deliberately independent from Docker execution, allowing
    callers to run it concurrently with sandbox testing.
    """
    prompt = load_prompt("complexity")
    payload = {
        "problem": public_problem_context(problem),
        "submission": {
            "language": language,
            "source_code": sanitize_code_comments(source_code),
        },
    }

    result = await invoke_agent(
        prompt,
        payload,
        ComplexityOutput,
        unavailable_analysis("The complexity analysis model was unavailable, so no complexity was inferred."),
    )
    if not result.get("time_complexity") and not result.get("space_complexity"):
        result = infer_static_complexity(source_code)
    return {
        "time_complexity": normalize_complexity(result.get("time_complexity")),
        "space_complexity": normalize_complexity(result.get("space_complexity")),
        "bottlenecks": result.get("bottlenecks") or [],
        "optimization_suggestion": result.get("optimization_suggestion") or "No optimization suggestion was available.",
        "reasoning": result.get("reasoning") or "No complexity analysis was available.",
    }


def score_complexity_analysis(
    analysis: Dict[str, Any], private_target: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Privately compare AI classification against the server-side target.

    ``private_target`` must only be created from the database in backend code.
    The response object intentionally contains no target complexity, rank or
    rank difference, so it is safe to persist and return to a student.
    """
    target_time = (private_target or {}).get("time")
    target_space = (private_target or {}).get("space")
    private_time_assessment = private_time_complexity_breakdown(
        target_time,
        analysis.get("time_complexity"),
    )
    private_space_assessment = private_space_complexity_breakdown(
        target_space,
        analysis.get("space_complexity"),
    )
    time_assessment = time_complexity_assessment(
        target_time,
        analysis.get("time_complexity"),
    )
    space_assessment = space_complexity_assessment(
        target_space,
        analysis.get("space_complexity"),
    )

    safe_details = {
        "time_complexity": time_assessment.get("student_time_complexity"),
        "space_complexity": space_assessment.get("student_space_complexity"),
        "time_score": time_assessment.get("time_score"),
        "time_score_max": 25,
        "time_classification": time_assessment.get("classification"),
        "time_status": time_assessment.get("status"),
        "space_score": space_assessment.get("space_score"),
        "space_score_max": 25,
        "space_classification": space_assessment.get("classification"),
        "space_status": space_assessment.get("status"),
        # Kept for compatibility with the existing result UI.
        "classification": time_assessment.get("classification"),
        "analysis_status": time_assessment.get("status"),
        "scoring_reason": time_assessment.get("reason"),
        "space_scoring_reason": space_assessment.get("reason"),
        "bottlenecks": analysis.get("bottlenecks") or [],
        "optimization_suggestion": analysis.get("optimization_suggestion") or "",
        "reasoning": analysis.get("reasoning") or "",
    }

    component_scores = [
        score
        for score in (
            time_assessment.get("score_percent"),
            space_assessment.get("score_percent"),
        )
        if score is not None
    ]

    return {
        "complexity_score": (
            round(sum(component_scores) / len(component_scores), 3)
            if component_scores
            else None
        ),
        "complexity_details": safe_details,
        # This does not reach the response schema or frontend. It is persisted
        # for staff/backend review when a student appears better than the
        # approved benchmark.
        "assessment_flags": {
            "benchmark_review_required": bool(
                private_time_assessment.get("benchmark_review_required")
                or private_space_assessment.get("benchmark_review_required")
            ),
        },
    }


async def complexity_node(state: EvaluationState) -> Dict[str, Any]:
    """Use the pre-started analysis when available, then score it privately."""
    analysis = state.get("precomputed_complexity_analysis")
    if not isinstance(analysis, dict):
        submission = state.get("submission") or {}
        analysis = await analyze_student_complexity(
            state.get("problem") or {},
            submission.get("source_code", ""),
            submission.get("language", ""),
        )

    scored = score_complexity_analysis(
        analysis,
        state.get("complexity_target"),
    )

    # A program that did not compile has no runnable algorithm to grade for
    # efficiency. A compile-successful partial/wrong-answer submission still
    # reaches the normal scoring path above.
    if (state.get("execution_result") or {}).get("compile_status") != "success":
        details = scored["complexity_details"]
        details.update(
            {
                "time_score": None,
                "space_score": None,
                "classification": "REVIEW_REQUIRED",
                "time_classification": "REVIEW_REQUIRED",
                "space_classification": "REVIEW_REQUIRED",
                "analysis_status": "NOT_SCORED_COMPILATION_FAILED",
                "time_status": "NOT_SCORED_COMPILATION_FAILED",
                "space_status": "NOT_SCORED_COMPILATION_FAILED",
                "scoring_reason": "Time complexity is not scored because the submission did not compile.",
            }
        )
        return {"complexity_score": None, "complexity_details": details}

    # Complexity is still analyzed for a partial submission, but code that
    # passes no test at all cannot receive efficiency marks merely because its
    # apparent Big-O looks good. Any positive correctness score keeps the
    # rank-distance score so partially correct work is still assessed.
    correctness_score = state.get("correctness_score")
    if correctness_score is not None and correctness_score <= 0:
        details = scored["complexity_details"]
        if (
            details.get("time_status") == "SCORED"
            or details.get("space_status") == "SCORED"
        ):
            details.update(
                {
                    "time_score": 0.0,
                    "space_score": 0.0 if details.get("space_score") is not None else None,
                    "classification": "NOT_AWARDED_INCORRECT",
                    "time_classification": "NOT_AWARDED_INCORRECT",
                    "space_classification": "NOT_AWARDED_INCORRECT",
                    "analysis_status": "NOT_AWARDED_NO_CORRECT_CASES",
                    "time_status": "NOT_AWARDED_NO_CORRECT_CASES",
                    "space_status": "NOT_AWARDED_NO_CORRECT_CASES",
                    "scoring_reason": "Time-complexity marks are not awarded because this submission passed no test cases.",
                }
            )
            return {"complexity_score": 0.0, "complexity_details": details}

    return scored
