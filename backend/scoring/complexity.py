"""Deterministic, private complexity scoring policy.

The LLM identifies the apparent complexity of the submitted code. This module
compares that observation with a curated target stored only in the backend
problem record. Target complexity is never part of an LLM payload or an API
response.
"""

from __future__ import annotations

import re
from typing import Any, Optional


TIME_COMPLEXITY_LEVELS = (
    "O(1)",
    "O(log n)",
    "O(sqrt n)",
    "O(n)",
    "O(n log n)",
    "O(n^2)",
    "O(n^3)",
    "O(n^4+)",
    "O(2^n)",
    "O(n!)",
)

# Kept as an alias for callers that used the previous name.
COMPLEXITY_LEVELS = list(TIME_COMPLEXITY_LEVELS)


def normalize_complexity(complexity: Optional[str]) -> Optional[str]:
    """Normalize common single-variable Big-O spellings.

    Multi-variable expressions such as ``O(V + E)`` and ``O(mn)`` are
    deliberately returned as unsupported values. They need a
    problem-family-specific comparator, not a global rank ladder.
    """
    if not complexity or not isinstance(complexity, str):
        return None

    raw = complexity.strip().lower()
    compact = raw
    compact = compact.replace("²", "^2").replace("³", "^3")
    compact = compact.replace("ⁿ", "^n").replace("√", "sqrt")
    compact = compact.replace("**", "^")
    compact = re.sub(r"\s+", "", compact)
    # Normalize common log spellings and harmless constant factors.
    compact = compact.replace("log₂", "log").replace("log10", "log")
    compact = compact.replace("log_2", "log").replace("log_10", "log")
    compact = compact.replace("ln", "log")
    compact = re.sub(r"^o\(\d+\*", "o(", compact)

    replacements = {
        "o(1)": "O(1)",
        "o(logn)": "O(log n)",
        "o(log2n)": "O(log n)",
        "o(log(n))": "O(log n)",
        "o(sqrtn)": "O(sqrt n)",
        "o(sqrt(n))": "O(sqrt n)",
        "o(n)": "O(n)",
        "o(nlogn)": "O(n log n)",
        "o(nlog(n))": "O(n log n)",
        "o(n^2)": "O(n^2)",
        "o(n2)": "O(n^2)",
        "o(n^3)": "O(n^3)",
        "o(n3)": "O(n^3)",
        "o(2^n)": "O(2^n)",
        "o(n!)": "O(n!)",
    }
    normalized = replacements.get(compact)
    if normalized:
        return normalized

    # Equivalent logarithmic bounds that use multiple input-size variables.
    # They remain logarithmic for the problem's input scale and can safely
    # enter the fixed ladder; other multi-variable expressions stay review-only.
    if re.fullmatch(r"o\(log\((min|max)\([a-z],?[a-z]\)\)\)", compact):
        return "O(log n)"
    if compact in {"o(log(m+n))", "o(log(m+n))"}:
        return "O(log n)"
    # For this platform, m+n represents the total input size and is mapped
    # to the single-size linear buckets used by the fixed scoring ladder.
    if compact in {"o(m+n)", "o(n+m)", "o(rows+cols)", "o(cols+rows)"}:
        return "O(n)"
    if compact in {
        "o((m+n)log(m+n))",
        "o((n+m)log(n+m))",
        "o(m+nlog(m+n))",
    }:
        return "O(n log n)"

    # The ladder intentionally buckets every polynomial above cubic into one
    # rank. This keeps O(n^4), O(n^5), and O(n^k) comparable without adding
    # unbounded ranks while preserving exponential and factorial levels.
    polynomial_match = re.fullmatch(r"o\(n\^(\d+)\)", compact)
    if polynomial_match and int(polynomial_match.group(1)) >= 4:
        return "O(n^4+)"
    polynomial_match = re.fullmatch(r"o\(n(\d+)\)", compact)
    if polynomial_match and int(polynomial_match.group(1)) >= 4:
        return "O(n^4+)"

    # Fixed ten-bucket projection of the wider asymptotic hierarchy. These
    # rules cover common logarithmic powers and fractional polynomial terms.
    if re.fullmatch(r"o\((log|loglog|logloglog|log\*)n?\)", compact):
        return "O(log n)"
    if re.fullmatch(r"o\(log\^\d+n\)", compact):
        return "O(log n)"
    if re.fullmatch(r"o\(\(?logn\)?\^\d+\)", compact):
        return "O(log n)"
    if compact in {"o(sqrtlogn)", "o(n^(1/4))", "o(n^(1/3))", "o(sqrtn)"}:
        return "O(sqrt n)"
    if compact in {"o(n/logn)", "o(n/log^2n)", "o(n^(1/2))"}:
        return "O(sqrt n)"
    if compact in {"o(nloglogn)", "o(nlog^2n)", "o(nlog^3n)", "o(n^(3/2))"}:
        return "O(n log n)"
    if compact in {"o(n^2/logn)", "o(n^2/log^2n)"}:
        return "O(n^2)"
    if compact in {"o(n^2loglogn)", "o(n^2logn)", "o(n^2log^2n)", "o(n^(5/2))"}:
        return "O(n^3)"
    if compact in {"o(n^3logn)", "o(n^3log^2n)"}:
        return "O(n^4+)"
    if re.fullmatch(r"o\(n\^\(logn\)\)", compact):
        return "O(n^4+)"
    if compact in {"o(2^sqrt(n))", "o(2^sqrt n)"}:
        return "O(n^4+)"
    if re.fullmatch(r"o\((2|3|4)\^n\*?n?(\^2)?\)", compact):
        return "O(2^n)"
    if re.fullmatch(r"o\(c\^n\)", compact):
        return "O(2^n)"
    return complexity.strip()


def complexity_rank(complexity: str) -> int:
    normalized = normalize_complexity(complexity)
    if normalized not in TIME_COMPLEXITY_LEVELS:
        raise ValueError(f"Unsupported single-variable complexity: {complexity}")
    # The approved assessment policy uses ranks 1 through 10, not zero-based
    # array indexes. This makes the stored rank and its explanation unambiguous.
    return TIME_COMPLEXITY_LEVELS.index(normalized) + 1


def private_time_complexity_breakdown(
    optimal_time: Optional[str], student_time: Optional[str]
) -> dict[str, Any]:
    """Calculate the complete rank-distance assessment inside the backend.

    The result includes private benchmark data and must never be returned from
    an API endpoint or added to an AI prompt. ``time_complexity_assessment``
    below creates the student-safe representation.
    """
    normalized_student = normalize_complexity(student_time)
    normalized_target = normalize_complexity(optimal_time)

    if not optimal_time:
        return {
            "status": "TARGET_NOT_CONFIGURED",
            "classification": "REVIEW_REQUIRED",
            "time_score": None,
            "score_percent": None,
            "student_time_complexity": normalized_student,
            "reason": "A verified complexity benchmark has not been configured for this problem.",
        }

    if not student_time:
        return {
            "status": "ANALYSIS_UNAVAILABLE",
            "classification": "REVIEW_REQUIRED",
            "time_score": None,
            "score_percent": None,
            "student_time_complexity": None,
            "reason": "The submitted algorithm could not be classified automatically.",
        }

    if (
        normalized_target not in TIME_COMPLEXITY_LEVELS
        or normalized_student not in TIME_COMPLEXITY_LEVELS
    ):
        return {
            "status": "REVIEW_REQUIRED",
            "classification": "REVIEW_REQUIRED",
            "time_score": None,
            "score_percent": None,
            "student_time_complexity": normalized_student,
            "reason": "This problem uses variables that require a problem-specific complexity comparison.",
        }

    optimal_rank = complexity_rank(normalized_target)
    student_rank = complexity_rank(normalized_student)
    difference = student_rank - optimal_rank
    # Ten levels create nine intervals between the best and worst ranks.
    penalty = 0.0 if difference <= 0 else min(25.0, difference * (25.0 / 9.0))
    marks = round(max(0.0, min(25.0, 25.0 - penalty)), 3)

    if difference <= 0:
        classification = "OPTIMAL"
    elif difference == 1:
        classification = "NEAR_OPTIMAL"
    elif difference <= 3:
        classification = "MODERATE"
    elif difference <= 5:
        classification = "INEFFICIENT"
    else:
        classification = "VERY_INEFFICIENT"

    return {
        "status": "SCORED",
        "classification": classification,
        "time_score": marks,
        "score_percent": round(marks * 4, 3),
        "student_time_complexity": normalized_student,
        # Private evaluation-only values. The wrapper removes them.
        "optimal_time_complexity": normalized_target,
        "student_rank": student_rank,
        "optimal_rank": optimal_rank,
        "difference": difference,
        "penalty": round(penalty, 3),
        "benchmark_review_required": difference < 0,
        "reason": "The detected time complexity was compared with the private benchmark for this problem.",
    }


def private_space_complexity_breakdown(
    optimal_space: Optional[str], student_space: Optional[str]
) -> dict[str, Any]:
    """Apply the same private 1–10 rank-distance policy to auxiliary space."""
    result = private_time_complexity_breakdown(optimal_space, student_space)
    result["student_space_complexity"] = result.get("student_time_complexity")
    if result.get("status") == "SCORED":
        result["reason"] = "The detected auxiliary-space complexity was compared with the private benchmark for this problem."
    return result


def time_complexity_assessment(
    optimal_time: Optional[str], student_time: Optional[str]
) -> dict[str, Any]:
    """Return the 25-mark time-complexity result without exposing targets.

    The returned value intentionally omits the target, its rank and the rank
    difference. Those values are private assessment data.
    """
    private = private_time_complexity_breakdown(optimal_time, student_time)
    return {
        "status": private["status"],
        "classification": private["classification"],
        "time_score": private["time_score"],
        "score_percent": private["score_percent"],
        "student_time_complexity": private["student_time_complexity"],
        "reason": private["reason"],
    }


def space_complexity_assessment(
    optimal_space: Optional[str], student_space: Optional[str]
) -> dict[str, Any]:
    """Create a student-safe 25-mark auxiliary-space assessment."""
    private = private_space_complexity_breakdown(optimal_space, student_space)
    return {
        "status": private["status"],
        "classification": private["classification"],
        "space_score": private["time_score"],
        "score_percent": private["score_percent"],
        "student_space_complexity": private["student_space_complexity"],
        "reason": private["reason"],
    }


def calculate_complexity_component_score(expected: str, student: str) -> float:
    """Legacy 0-100 wrapper for the new time-score policy."""
    result = time_complexity_assessment(expected, student)
    if result["score_percent"] is None:
        raise ValueError("Complexity requires problem-specific review")
    return float(result["score_percent"])


def calculate_complexity_score(
    expected_time: str,
    student_time: str,
    expected_space: str,
    student_space: str,
) -> float:
    """Compatibility wrapper; the active policy scores time only (/25)."""
    del expected_space, student_space
    return calculate_complexity_component_score(expected_time, student_time)
