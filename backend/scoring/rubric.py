"""Versioned shared assessment policy. Similarity never contributes marks."""
from __future__ import annotations
import math
from typing import Any, Mapping

RUBRIC_VERSION = "complexity-focused-v2"
DEFAULT_WEIGHT_PERCENT = {"correctness": 30.0, "time": 35.0, "space": 25.0, "style": 10.0}
STUDENT_RUBRIC_WEIGHTS = {key: value / 100 for key, value in DEFAULT_WEIGHT_PERCENT.items()}
INSTRUCTOR_RUBRIC_WEIGHTS = STUDENT_RUBRIC_WEIGHTS


def _clamp(value: Any) -> float | None:
    try:
        parsed = float(value)
        return max(0.0, min(100.0, parsed)) if math.isfinite(parsed) else None
    except (TypeError, ValueError):
        return None


def validate_weights(weights: Mapping | None = None) -> dict[str, float]:
    if weights is None:
        return dict(DEFAULT_WEIGHT_PERCENT)
    if set(weights) != set(DEFAULT_WEIGHT_PERCENT):
        raise ValueError("Provide correctness, time, space and style weights")
    result = {key: float(weights[key]) for key in DEFAULT_WEIGHT_PERCENT}
    if any(not math.isfinite(v) or v < 0 or v > 100 for v in result.values()):
        raise ValueError("Weights must be finite percentages between 0 and 100")
    if not math.isclose(sum(result.values()), 100.0, abs_tol=1e-6):
        raise ValueError("Scoring weights must total 100%")
    return result


def complexity_dimension_percent(details: Any, dimension: str) -> float | None:
    if not isinstance(details, Mapping):
        return None
    try:
        maximum = float(details.get(f"{dimension}_score_max", 25))
        score = float(details.get(f"{dimension}_score"))
        return _clamp(score / maximum * 100) if math.isfinite(maximum) and maximum > 0 else None
    except (TypeError, ValueError):
        return None


def student_rubric_score(correctness, complexity_details, style, weights=None):
    """S=min(weighted sum,correctness). Missing weights are never redistributed."""
    percentages = validate_weights(weights)
    components = {"correctness": _clamp(correctness),
                  "time": complexity_dimension_percent(complexity_details, "time"),
                  "space": complexity_dimension_percent(complexity_details, "space"), "style": _clamp(style)}
    missing = [key for key, value in components.items() if value is None and (percentages[key] > 0 or key == "correctness")]
    breakdown = {}
    known = 0.0
    for key, value in components.items():
        weight = percentages[key] / 100
        contribution = None if value is None and weight > 0 else (value or 0) * weight
        known += contribution or 0
        breakdown[key] = {"score": value, "weight": weight, "effective_weight": weight,
                          "weighted": round(contribution, 4) if contribution is not None else None}
    c = components["correctness"]
    ceiling = c if c is not None else 100.0
    lower = min(known, c) if c is not None else 0.0
    upper = min(known + sum(percentages[key] for key in missing), ceiling)
    raw = round(known, 1) if not missing else None
    # Round marks for display without rounding a partial correctness ceiling
    # upward. In particular 99.999% correctness must never become 100 points.
    def bounded_mark(value):
        return min(round(min(value, ceiling), 1), math.floor(ceiling * 10) / 10)
    final = 0.0 if c == 0 else (bounded_mark(known) if not missing else None)
    breakdown["correctness_gate"] = {"raw_score": raw, "score_before_cap": raw, "score_cap": c,
        "final_score": final, "accepted": None if c is None else c == 100, "rule": "min(weighted_score, correctness)"}
    breakdown["assessment"] = {"status": "incomplete" if missing else "complete", "missing_components": missing,
                               "score_lower_bound": bounded_mark(lower), "score_upper_bound": bounded_mark(upper)}
    breakdown["rubric"] = {"version": RUBRIC_VERSION, "weights": percentages, "correctness_ceiling": True,
                          "rounding": "one_decimal_without_crossing_correctness_ceiling"}
    return final, breakdown


def instructor_rubric_score(correctness, complexity_details, style, similarity=None, weights=None):
    """Faculty see the same mark; similarity is separate review evidence."""
    return student_rubric_score(correctness, complexity_details, style, weights)
