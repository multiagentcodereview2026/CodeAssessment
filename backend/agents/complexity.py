from pydantic import BaseModel
from typing import List, Dict, Any

from agents.base import load_prompt, invoke_agent
from workflow.state import EvaluationState

from scoring.complexity import (
    calculate_complexity_score,
    calculate_complexity_component_score,
    normalize_complexity,
)


class ComplexityOutput(BaseModel):
    time_complexity: str | None
    space_complexity: str | None
    bottlenecks: List[str]
    optimization_suggestion: str
    reasoning: str


def extract_expected_complexities(
    problem: Dict[str, Any]
) -> tuple[str | None, str | None]:
    """
    Extract explicitly stated expected time and space complexity
    from the problem description.

    We only use requirements that are explicitly stated.
    We never invent a complexity requirement.
    """

    import re

    constraints = problem.get("constraints") or ""
    if isinstance(constraints, (list, tuple)):
        constraints = "\n".join(str(item) for item in constraints)

    text = "\n".join(
        str(value)
        for value in (
            problem.get("description"),
            problem.get("statement"),
            constraints,
        )
        if value
    )

    expected_time = None
    expected_space = None

    complexity_pattern = (
        r"O\s*\(\s*"
        r"(?:"
        r"log\s*n|"
        r"n\s*log\s*n|"
        r"n\s*\^\s*2|"
        r"n\s*\^\s*3|"
        r"2\s*\^\s*n|"
        r"n!|"
        r"n|"
        r"1"
        r")"
        r"\s*\)"
    )

    # ---------------------------------------------------------
    # TIME COMPLEXITY
    # ---------------------------------------------------------

    # Forms: "O(n) time complexity" and "O(n) time required"
    time_before = re.search(
        rf"({complexity_pattern})\s*"
        r"(?:time|runtime)(?:\s+(?:complexity|required|limit))?",
        text,
        flags=re.IGNORECASE,
    )

    # Forms: "time complexity O(n)" and "time required: O(n)"
    time_after = re.search(
        rf"(?:time|runtime)(?:\s+(?:complexity|required|limit))?\s*"
        rf"[:\-]?\s*({complexity_pattern})",
        text,
        flags=re.IGNORECASE,
    )

    if time_before:
        expected_time = normalize_complexity(time_before.group(1))
    elif time_after:
        expected_time = normalize_complexity(time_after.group(1))

    # ---------------------------------------------------------
    # SPACE COMPLEXITY
    # ---------------------------------------------------------

    # Forms: "O(1) space complexity" and "O(1) memory required"
    space_before = re.search(
        rf"({complexity_pattern})\s*"
        r"(?:space|memory)(?:\s+(?:complexity|required|limit))?",
        text,
        flags=re.IGNORECASE,
    )

    # Forms: "space complexity O(1)" and "memory required: O(1)"
    space_after = re.search(
        rf"(?:space|memory)(?:\s+(?:complexity|required|limit))?\s*"
        rf"[:\-]?\s*({complexity_pattern})",
        text,
        flags=re.IGNORECASE,
    )

    if space_before:
        expected_space = normalize_complexity(space_before.group(1))
    elif space_after:
        expected_space = normalize_complexity(space_after.group(1))

    return expected_time, expected_space


async def complexity_node(state: EvaluationState) -> Dict[str, Any]:
    prompt = load_prompt("complexity")

    problem = state.get("problem") or {}
    source_code = state.get("submission", {}).get("source_code", "")

    expected_time, expected_space = extract_expected_complexities(problem)

    payload = {
        "problem": problem,
        "source_code": source_code,
        "expected_time_complexity": expected_time,
        "expected_space_complexity": expected_space,
    }

    fallback = {
    "time_complexity": None,
    "space_complexity": None,
    "bottlenecks": [
        "Complexity analysis was unavailable."
    ],
    "optimization_suggestion": (
        "Retry the assessment to obtain algorithmic complexity analysis."
    ),
    "reasoning": (
        "The complexity analysis model was unavailable, "
        "so no complexity was inferred."
    ),
}

    result = await invoke_agent(
        prompt,
        payload,
        ComplexityOutput,
        fallback,
    )

    student_time = result.get("time_complexity")
    student_space = result.get("space_complexity")

    complexity_score = None

    if student_time is not None:
        try:
            if (
                expected_time is not None
                and expected_space is not None
                and student_space is not None
            ):
                complexity_score = calculate_complexity_score(
                    expected_time=expected_time,
                    student_time=student_time,
                    expected_space=expected_space,
                    student_space=student_space,
                )

            elif expected_time is not None:
                complexity_score = calculate_complexity_component_score(
                    expected_time,
                    student_time,
                )

        except ValueError:
            complexity_score = None

    result["complexity_score"] = complexity_score
    result["expected_time_complexity"] = expected_time
    result["expected_space_complexity"] = expected_space

    return {
        "complexity_score": complexity_score,
        "complexity_details": result,
    }
