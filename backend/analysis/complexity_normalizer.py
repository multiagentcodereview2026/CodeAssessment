import re


# Fixed ranking used for deterministic scoring.
# Rank 1 is best; rank 10 is worst.
COMPLEXITY_RANKS = {
    "O(1)": 1,
    "O(log n)": 2,
    "O(sqrt(n))": 3,
    "O(n)": 4,
    "O(n log n)": 5,
    "O(n^2)": 6,
    "O(n^3)": 7,
    "O(n^4+)": 8,
    "O(2^n)": 9,
    "O(n!)": 10,
}


def normalize_complexity(value: str | None) -> str | None:
    if not value:
        return None

    text = value.strip().lower()
    text = text.replace(" ", "")
    text = text.replace("²", "^2")
    text = text.replace("³", "^3")
    text = text.replace("⁴", "^4")
    text = text.replace("∞", "inf")

    if text in {"o(1)", "1", "constant"}:
        return "O(1)"

    if "log" in text and "n" in text and "^2" not in text:
        if text in {"o(logn)", "o(log(n))"}:
            return "O(log n)"

    if text in {"o(sqrt(n))", "o(sqrtn)", "o(√n)"}:
        return "O(sqrt(n))"

    if text in {"o(n)", "o(n+ m)", "o(n+m)"}:
        return "O(n)"

    if text in {"o(nlogn)", "o(nlog(n))"}:
        return "O(n log n)"

    if text in {"o(n^2)", "o(n*n)", "o(n²)"}:
        return "O(n^2)"

    if text in {"o(n^3)", "o(n*n*n)", "o(n³)"}:
        return "O(n^3)"

    # Any polynomial higher than cubic is grouped into rank 8.
    match = re.search(r"n\^(\d+)", text)
    if match and int(match.group(1)) >= 4:
        return "O(n^4+)"

    if text in {"o(2^n)", "o(2n)", "o(2**n)"}:
        return "O(2^n)"

    if text in {"o(n!)"}:
        return "O(n!)"

    # Preserve recognized multi-variable expressions for review.
    if text.startswith("o("):
        return value.strip()

    return None


def complexity_rank(value: str | None) -> int | None:
    normalized = normalize_complexity(value)
    return COMPLEXITY_RANKS.get(normalized)


def rank_distance(student: str | None, optimal: str | None) -> int | None:
    student_rank = complexity_rank(student)
    optimal_rank = complexity_rank(optimal)

    if student_rank is None or optimal_rank is None:
        return None

    return max(0, student_rank - optimal_rank)


def score_complexity(
    student: str | None,
    optimal: str | None,
    maximum_score: float = 25.0,
) -> float | None:
    difference = rank_distance(student, optimal)

    if difference is None:
        return None

    penalty_per_level = maximum_score / 9
    score = maximum_score - (difference * penalty_per_level)

    return round(max(0.0, min(maximum_score, score)), 3)