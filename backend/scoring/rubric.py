"""Deterministic scoring policy shared by the assessment and staff views.

Student marks must be based only on the work visible in the student rubric.
Similarity remains persisted for staff review, but is deliberately excluded from
the student score.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional


STUDENT_RUBRIC_WEIGHTS = {
    "correctness": 0.20,
    "time": 0.30,
    "space": 0.30,
    "style": 0.20,
}

# A submission that is not accepted can still receive credit for efficient,
# maintainable work, but it must not be presented as an excellent solution.
NON_ACCEPTED_SCORE_CAP = 79.0

# The instructor score is a review metric, not a replacement for the student
# grade.  Its final component is originality (100 - similarity risk).
INSTRUCTOR_RUBRIC_WEIGHTS = {
    "correctness": 0.20,
    "time": 0.25,
    "space": 0.25,
    "style": 0.20,
    "originality": 0.10,
}


def _clamp(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return None


def complexity_dimension_percent(details: Any, dimension: str) -> Optional[float]:
    """Return one complexity dimension as a percentage, if evidence exists."""
    if not isinstance(details, Mapping):
        return None
    score = details.get(f"{dimension}_score")
    maximum = details.get(f"{dimension}_score_max", 25)
    try:
        score = float(score)
        maximum = float(maximum)
    except (TypeError, ValueError):
        return None
    if maximum <= 0:
        return None
    return _clamp(score / maximum * 100)


def weighted_rubric_score(
    components: Mapping[str, Optional[float]],
    weights: Mapping[str, float],
) -> tuple[float, dict[str, dict[str, float | None]]]:
    """Calculate a score and an auditable breakdown.

    When a dimension is unavailable, its weight is proportionally shared by
    available dimensions. This keeps a missing analyser from silently acting as
    a zero while still preserving declared and effective weights in the result.
    """
    normalized = {name: _clamp(components.get(name)) for name in weights}
    available_weight = sum(weights[name] for name, value in normalized.items() if value is not None)
    if not available_weight:
        return 0.0, {
            name: {"score": normalized[name], "weight": weights[name], "effective_weight": 0.0, "weighted": 0.0}
            for name in weights
        }

    breakdown: dict[str, dict[str, float | None]] = {}
    total = 0.0
    for name, declared_weight in weights.items():
        score = normalized[name]
        effective_weight = declared_weight / available_weight if score is not None else 0.0
        weighted = (score or 0.0) * effective_weight
        total += weighted
        breakdown[name] = {
            "score": score,
            "weight": declared_weight,
            "effective_weight": effective_weight,
            "weighted": round(weighted, 2),
        }
    return round(total, 1), breakdown


def student_rubric_score(
    correctness: Any,
    complexity_details: Any,
    style: Any,
) -> tuple[float, dict[str, dict[str, float | None]]]:
    raw_score, breakdown = weighted_rubric_score(
        {
            "correctness": correctness,
            "time": complexity_dimension_percent(complexity_details, "time"),
            "space": complexity_dimension_percent(complexity_details, "space"),
            "style": style,
        },
        STUDENT_RUBRIC_WEIGHTS,
    )
    correctness_percent = _clamp(correctness) or 0.0
    correctness_factor = correctness_percent / 100.0
    score_before_cap = round(raw_score * correctness_factor, 1)
    accepted = correctness_percent >= 100.0
    score_cap = None if accepted else NON_ACCEPTED_SCORE_CAP
    final_score = min(score_before_cap, score_cap) if score_cap is not None else score_before_cap
    breakdown["correctness_gate"] = {
        "raw_score": raw_score,
        "correctness_factor": round(correctness_factor, 4),
        "score_before_cap": score_before_cap,
        "score_cap": score_cap,
        "final_score": final_score,
        "accepted": accepted,
    }
    return final_score, breakdown


def instructor_rubric_score(
    correctness: Any,
    complexity_details: Any,
    style: Any,
    similarity: Any,
) -> tuple[float, dict[str, dict[str, float | None]]]:
    similarity_percent = _clamp(similarity)
    return weighted_rubric_score(
        {
            "correctness": correctness,
            "time": complexity_dimension_percent(complexity_details, "time"),
            "space": complexity_dimension_percent(complexity_details, "space"),
            "style": style,
            "originality": None if similarity_percent is None else 100.0 - similarity_percent,
        },
        INSTRUCTOR_RUBRIC_WEIGHTS,
    )
