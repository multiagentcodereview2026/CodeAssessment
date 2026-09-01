def calculate_final_score(
    correctness_score: float,
    complexity_score: float,
    style_score: float,
    originality_score: float
) -> float:
    """
    Calculate the overall assessment score.

    Weights:
    Correctness  : 40%
    Complexity   : 20%
    Style        : 20%
    Originality  : 20%
    """

    final_score = (
        correctness_score * 0.40
        + complexity_score * 0.20
        + style_score * 0.20
        + originality_score * 0.20
    )

    return round(final_score, 2)