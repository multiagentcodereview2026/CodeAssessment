COMPLEXITY_LEVELS = [
    "O(1)",
    "O(log n)",
    "O(n)",
    "O(n log n)",
    "O(n^2)",
    "O(n^3)",
    "O(2^n)",
    "O(n!)"
]


def normalize_complexity(complexity: str) -> str:
    """
    Normalize common formatting variations of complexity notation.
    """

    complexity = complexity.strip().lower()

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
        "o(n!)": "O(n!)"
    }

    return replacements.get(complexity, complexity)


def complexity_rank(complexity: str) -> int:
    """
    Return the position of a complexity in our ordered scale.
    Lower rank means better asymptotic complexity.
    """

    normalized = normalize_complexity(complexity)

    if normalized not in COMPLEXITY_LEVELS:
        raise ValueError(
            f"Unsupported complexity: {complexity}"
        )

    return COMPLEXITY_LEVELS.index(normalized)


def calculate_complexity_component_score(
    expected: str,
    student: str
) -> float:
    """
    Calculate a 0-100 score for either time or space complexity.
    """

    expected_rank = complexity_rank(expected)
    student_rank = complexity_rank(student)

    # Student is equal to or better than expected.
    if student_rank <= expected_rank:
        return 100.0

    # Student is worse than expected.
    difference = student_rank - expected_rank

    score = 100 - (difference * 20)

    return max(0.0, float(score))


def calculate_complexity_score(
    expected_time: str,
    student_time: str,
    expected_space: str,
    student_space: str
) -> float:

    time_score = calculate_complexity_component_score(
        expected_time,
        student_time
    )

    space_score = calculate_complexity_component_score(
        expected_space,
        student_space
    )

    # Time is more important than auxiliary space.
    final_score = (
        time_score * 0.7
        + space_score * 0.3
    )

    return round(final_score, 2)