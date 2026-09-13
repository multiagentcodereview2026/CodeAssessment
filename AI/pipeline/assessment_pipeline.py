import json

from agents.correctness_agent import analyze_correctness
from agents.complexity_agent import analyze_complexity
from agents.style_agent import analyze_style

from scoring.correctness_scorer import calculate_correctness_score
from scoring.complexity_scorer import calculate_complexity_score
from scoring.style_scorer import calculate_style_score
from scoring.similarity_scorer import (
    calculate_similarity,
    calculate_originality,
)
from scoring.score_aggregator import calculate_final_score

from assessment_result import AssessmentResult, AssessmentScores


def assess_submission(
    problem,
    code,
    language,
    execution_result,
    reference_code=None
) -> AssessmentResult:

    problem_text = f"""
Problem ID:
{problem.problem_id}

Title:
{problem.title}

Description:
{problem.description}

Expected Time Complexity:
{problem.expected_time_complexity}

Expected Space Complexity:
{problem.expected_space_complexity}
"""

    execution_text = json.dumps(
        execution_result.model_dump(),
        indent=2
    )

    # AI-based explanations
    correctness_result = analyze_correctness(
        problem=problem_text,
        code=code,
        execution_results=execution_text,
        language=language
    )

    complexity_result = analyze_complexity(
        problem=problem_text,
        code=code,
        language=language
    )

    style_result = analyze_style(
        problem=problem_text,
        code=code,
        language=language
    )

    # Deterministic scores
    correctness_score = calculate_correctness_score(
        execution_result,
        problem.test_cases
    )

    complexity_score = calculate_complexity_score(
        problem.expected_time_complexity,
        complexity_result.time_complexity,
        problem.expected_space_complexity,
        complexity_result.space_complexity
    )

    style_score = calculate_style_score(style_result)

    # Similarity/originality
    if reference_code:
        similarity_score = calculate_similarity(
            code,
            reference_code
        )

        originality_score = calculate_originality(
            similarity_score
        )

        similarity_status = "evaluated"

    else:
        similarity_score = None
        originality_score = None
        similarity_status = "reference code not provided"

    # Use zero originality contribution when no reference code exists
    originality_for_final_score = (
        originality_score
        if originality_score is not None
        else 0.0
    )

    final_score = calculate_final_score(
        correctness_score,
        complexity_score,
        style_score,
        originality_for_final_score
    )

    scores = AssessmentScores(
        correctness=correctness_score,
        complexity=complexity_score,
        style=style_score,
        similarity=similarity_score,
        originality=originality_score,
        final=final_score
    )

    assessment_result = AssessmentResult(
        correctness=correctness_result,
        complexity=complexity_result,
        style=style_result,
        scores=scores,
        similarity_status=similarity_status
    )

    return assessment_result