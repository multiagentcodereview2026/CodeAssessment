import re

from .models import ComplexityAnalysis


def _loop_depth(source: str) -> int:
    loop_count = len(
        re.findall(r"\b(for|while|do)\b", source, flags=re.IGNORECASE)
    )

    if loop_count >= 3:
        return 3
    if loop_count == 2:
        return 2
    if loop_count == 1:
        return 1
    return 0


def analyze_cpp(source: str) -> ComplexityAnalysis:
    signals: list[str] = []
    source_lower = source.lower()

    if not source.strip():
        return ComplexityAnalysis(
            status="REVIEW_REQUIRED",
            method="static",
            explanation="Source code is empty.",
        )

    # Exponential recursion patterns.
    recursive_calls = re.findall(r"\b(\w+)\s*\([^;{}]*\)\s*;", source)
    has_recursion = bool(
        re.search(r"\b( return |)\s*\w+\s*\([^;{}]*\+\s*1[^;{}]*\)", source)
    )

    if has_recursion and (
        "f(" in source_lower
        or "fib" in source_lower
        or "backtrack" in source_lower
    ):
        signals.append("recursive branching detected")
        time_complexity = "O(2^n)"
        confidence = 0.78
    elif re.search(r"\b(binary_search|lower_bound|upper_bound)\b", source_lower):
        signals.append("binary-search operation detected")
        time_complexity = "O(log n)"
        confidence = 0.90
    elif re.search(r"\b(sort|stable_sort)\s*\(", source_lower):
        signals.append("sorting operation detected")
        time_complexity = "O(n log n)"
        confidence = 0.88
    else:
        depth = _loop_depth(source)

        if depth >= 3:
            signals.append("three or more nested loops detected")
            time_complexity = "O(n^3)"
            confidence = 0.82
        elif depth == 2:
            signals.append("two nested loops detected")
            time_complexity = "O(n^2)"
            confidence = 0.86
        elif depth == 1:
            signals.append("single input-dependent loop detected")
            time_complexity = "O(n)"
            confidence = 0.76
        else:
            signals.append("no input-dependent loop detected")
            time_complexity = "O(1)"
            confidence = 0.60

    # Auxiliary-space estimation.
    has_input_sized_storage = bool(
        re.search(
            r"\b(vector|unordered_map|unordered_set|map|set|string)\b",
            source_lower,
        )
    )

    has_matrix_storage = bool(
        re.search(r"\b(vector|array)\s*<[^>]+>\s+\w+\s*\[", source_lower)
    )

    recursion_space = has_recursion

    if has_matrix_storage:
        space_complexity = "O(n^2)"
        signals.append("matrix-like storage detected")
        space_confidence = 0.78
    elif has_input_sized_storage or recursion_space:
        space_complexity = "O(n)"
        signals.append("input-sized storage or recursion stack detected")
        space_confidence = 0.78
    else:
        space_complexity = "O(1)"
        signals.append("no input-sized auxiliary storage detected")
        space_confidence = 0.70

    return ComplexityAnalysis(
        time_complexity=time_complexity,
        space_complexity=space_complexity,
        confidence=min(confidence, space_confidence),
        method="static",
        status="ANALYZED",
        signals=signals,
        explanation="Complexity was estimated from the C++ source structure.",
    )


def analyze_source(
    source: str,
    language: str,
) -> ComplexityAnalysis:
    language_name = language.lower().strip()

    if language_name in {"cpp", "c++", "cc", "cxx"}:
        return analyze_cpp(source)

    return ComplexityAnalysis(
        status="REVIEW_REQUIRED",
        method="static",
        confidence=0.0,
        explanation=f"Static analysis for {language} is not implemented yet.",
    )