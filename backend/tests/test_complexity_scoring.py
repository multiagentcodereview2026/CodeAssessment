import asyncio

from agents.complexity import complexity_node
from agents.complexity import infer_static_complexity
from scoring.complexity import (
    complexity_rank,
    normalize_complexity,
    private_time_complexity_breakdown,
    space_complexity_assessment,
    time_complexity_assessment,
)


def test_normalizes_common_big_o_spellings():
    assert normalize_complexity("O(nlogn)") == "O(n log n)"
    assert normalize_complexity("O(√n)") == "O(sqrt n)"
    assert normalize_complexity("O(n²)") == "O(n^2)"


def test_theta_is_not_silently_mixed_into_big_o_scoring():
    assessment = time_complexity_assessment("O(n)", "Θ(n)")
    assert assessment["status"] == "REVIEW_REQUIRED"
    assert assessment["time_score"] is None


def test_time_score_is_optimal_when_student_matches_target():
    assessment = time_complexity_assessment("O(n)", "O(n)")
    assert assessment["time_score"] == 25
    assert assessment["score_percent"] == 100.0
    assert assessment["classification"] == "OPTIMAL"


def test_time_score_uses_the_approved_ladder():
    assert time_complexity_assessment("O(n)", "O(n log n)")["time_score"] == 22.222
    assert time_complexity_assessment("O(n)", "O(n^2)")["time_score"] == 19.444
    assert time_complexity_assessment("O(log n)", "O(n^2)")["time_score"] == 13.889
    assert time_complexity_assessment("O(n)", "O(n!)")["time_score"] == 8.333
    assert time_complexity_assessment("O(1)", "O(n!)")["time_score"] == 0.0


def test_polynomial_complexities_above_cubic_share_rank_eight():
    assert normalize_complexity("O(n^4)") == "O(n^4+)"
    assert normalize_complexity("O(n^7)") == "O(n^4+)"
    assert complexity_rank("O(n^4)") == 8
    assert complexity_rank("O(n^4)") == complexity_rank("O(n^6)")
    assert time_complexity_assessment("O(n)", "O(n^4)")["time_score"] == 13.889


def test_extended_hierarchy_projects_into_fixed_ten_buckets():
    assert normalize_complexity("O(log_2 n)") == "O(log n)"
    assert normalize_complexity("O(log(min(m,n)))") == "O(log n)"
    assert normalize_complexity("O(log(m+n))") == "O(log n)"
    assert normalize_complexity("O(m+n)") == "O(n)"
    assert normalize_complexity("O((m+n) log(m+n))") == "O(n log n)"
    assert normalize_complexity("O((log n)^3)") == "O(log n)"
    assert normalize_complexity("O(n / log n)") == "O(sqrt n)"
    assert normalize_complexity("O(n log^2 n)") == "O(n log n)"
    assert normalize_complexity("O(n^2 log n)") == "O(n^3)"
    assert normalize_complexity("O(n^3 log n)") == "O(n^4+)"
    assert normalize_complexity("O(2^sqrt(n))") == "O(n^4+)"
    assert normalize_complexity("O(3^n)") == "O(2^n)"


def test_space_score_uses_the_same_rank_distance_rule():
    assessment = space_complexity_assessment("O(n)", "O(n^2)")
    assert assessment["space_score"] == 19.444
    assert assessment["score_percent"] == 77.776


def test_rank_is_one_based_and_better_than_target_is_flagged_for_review():
    assert complexity_rank("O(1)") == 1
    assert complexity_rank("O(n)") == 4
    assert complexity_rank("O(n^4)") == 8
    assert complexity_rank("O(2^n)") == 9
    assert complexity_rank("O(n!)") == 10

    private = private_time_complexity_breakdown("O(n)", "O(log n)")
    assert private["time_score"] == 25.0
    assert private["benchmark_review_required"] is True


def test_multivariable_complexity_requires_problem_specific_review():
    assessment = time_complexity_assessment("O(V + E)", "O(V^2)")
    assert assessment["status"] == "REVIEW_REQUIRED"
    assert assessment["classification"] == "REVIEW_REQUIRED"
    assert assessment["time_score"] is None
    assert assessment["score_percent"] is None
    assert "O(V + E)" not in str(assessment)


def test_no_private_target_means_no_complexity_penalty():
    assessment = time_complexity_assessment(None, "O(n^2)")
    assert assessment["status"] == "TARGET_NOT_CONFIGURED"
    assert assessment["time_score"] is None


def test_static_fallback_handles_linear_merge_without_ai():
    result = infer_static_complexity(
        "vector<int> merged; while (i < m) merged.push_back(a[i++]);"
    )
    assert result["time_complexity"] == "O(n)"
    assert result["space_complexity"] == "O(n)"


def test_compile_failure_does_not_receive_a_complexity_mark():
    result = asyncio.run(
        complexity_node(
            {
                "execution_result": {"compile_status": "error"},
                "complexity_target": {"time": "O(n)", "space": "O(1)"},
                "precomputed_complexity_analysis": {
                    "time_complexity": "O(n)",
                    "space_complexity": "O(1)",
                    "bottlenecks": [],
                    "optimization_suggestion": "",
                    "reasoning": "",
                },
            }
        )
    )

    assert result["complexity_score"] is None
    assert result["complexity_details"]["time_score"] is None
    assert result["complexity_details"]["space_score"] is None
    assert result["complexity_details"]["analysis_status"] == "NOT_SCORED_COMPILATION_FAILED"


def test_zero_correct_cases_receive_no_efficiency_marks():
    result = asyncio.run(
        complexity_node(
            {
                "execution_result": {"compile_status": "success"},
                "correctness_score": 0.0,
                "complexity_target": {"time": "O(n)", "space": "O(1)"},
                "precomputed_complexity_analysis": {
                    "time_complexity": "O(n)",
                    "space_complexity": "O(1)",
                    "bottlenecks": [],
                    "optimization_suggestion": "",
                    "reasoning": "",
                },
            }
        )
    )

    assert result["complexity_score"] == 0.0
    assert result["complexity_details"]["time_score"] == 0.0
    assert result["complexity_details"]["space_score"] == 0.0
    assert result["complexity_details"]["analysis_status"] == "NOT_AWARDED_NO_CORRECT_CASES"
