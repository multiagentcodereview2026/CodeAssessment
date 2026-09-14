COMPLEXITY_LEVELS = [
    "O(1)",
    "O(log n)",
    "O(n)",
    "O(n log n)",
    "O(n^2)",
    "O(n^3)",
    "O(2^n)",
    "O(n!)",
]


def normalize_complexity(complexity: str) -> str:
    """Normalize supported Big-O notation into a canonical form."""
    normalized = complexity.strip().lower()
    replacements = {
        "o(1)": "O(1)",
        "o(log n)": "O(log n)",
        "o(n)": "O(n)",
        "o(n log n)": "O(n log n)",
        "o(n^2)": "O(n^2)",
        "o(n²)": "O(n^2)",
        "o(n^3)": "O(n^3)",
        "o(n³)": "O(n^3)",
        "o(2^n)": "O(2^n)",
        "o(2ⁿ)": "O(2^n)",
        "o(n!)": "O(n!)",
    }
    return replacements.get(normalized, normalized)


def complexity_rank(complexity: str) -> int:
    normalized = normalize_complexity(complexity)
    if normalized not in COMPLEXITY_LEVELS:
        raise ValueError(f"Unsupported complexity: {complexity}")
    return COMPLEXITY_LEVELS.index(normalized)


def calculate_complexity_component_score(expected: str, student: str) -> float:
    """Score one time or auxiliary-space complexity requirement."""
    difference = complexity_rank(student) - complexity_rank(expected)
    if difference <= 0:
        return 100.0
    return max(0.0, float(100 - (difference * 20)))


def calculate_complexity_score(
    expected_time: str,
    student_time: str,
    expected_space: str,
    student_space: str,
) -> float:
    """Weight time at 70% and auxiliary space at 30%."""
    time_score = calculate_complexity_component_score(expected_time, student_time)
    space_score = calculate_complexity_component_score(expected_space, student_space)
    return round((time_score * 0.7) + (space_score * 0.3), 2)
