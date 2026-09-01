from schemas import StyleResult


def calculate_style_score(result: StyleResult) -> float:
    """
    Calculate the final style score from the individual
    style component scores.

    Weights:
    - Readability: 30%
    - Naming: 25%
    - Maintainability: 30%
    - Documentation: 15%
    """

    score = (
        result.readability_score * 0.30
        + result.naming_score * 0.25
        + result.maintainability_score * 0.30
        + result.documentation_score * 0.15
    )

    return round(score, 2)