import asyncio

from agents.complexity import complexity_node
from agents.complexity import infer_static_complexity
from scoring.complexity import (
    bounded_parameters_from_constraints,
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
    assert normalize_complexity(r"O(|\Sigma|)") == "O(1)"


def test_normalizes_any_single_symbolic_input_variable_to_n():
    # Keep the student's exact notation in the report; rank it privately.
    assert normalize_complexity("O(L)") == "O(L)"
    assert normalize_complexity("O(M^2)") == "O(M^2)"
    assert normalize_complexity("O(log P)") == "O(log P)"
    assert normalize_complexity("O(q log q)") == "O(q log q)"
    assert normalize_complexity("O(2^V)") == "O(2^V)"
    assert normalize_complexity("O(N + 26n)") == "O(N + 26n)"

    linear = time_complexity_assessment("O(n)", "O(L)")
    assert linear["status"] == "SCORED"
    assert linear["time_score"] == 25.0

    aggregate = time_complexity_assessment("O(n)", "O(N + Σ|word|)")
    assert aggregate["student_time_complexity"] == "O(N + Σ|word|)"
    assert aggregate["status"] == "SCORED"
    assert aggregate["time_score"] == 25.0

    # Two independently sized inputs cannot be collapsed into one n.
    multi = time_complexity_assessment("O(n)", "O(M*N)")
    assert multi["status"] == "REVIEW_REQUIRED"


def test_theta_is_not_silently_mixed_into_big_o_scoring():
    assessment = time_complexity_assessment("O(n)", "Θ(n)")
    assert assessment["status"] == "REVIEW_REQUIRED"
    assert assessment["time_score"] is None


def test_time_score_is_optimal_when_student_matches_target():
    assessment = time_complexity_assessment("O(n)", "O(n)")
    assert assessment["time_score"] == 25
    assert assessment["score_percent"] == 100.0
    assert assessment["classification"] == "OPTIMAL"


def test_time_score_uses_the_benchmark_relative_ladder():
    # Each slower rank consumes an equal share of the ranks below the
    # benchmark, so the same rank difference is more serious for a stronger
    # benchmark such as O(n) than for O(1).
    assert time_complexity_assessment("O(n)", "O(n log n)")["time_score"] == 20.833
    assert time_complexity_assessment("O(n)", "O(n^2)")["time_score"] == 16.667
    assert time_complexity_assessment("O(log n)", "O(n^2)")["time_score"] == 12.5
    assert time_complexity_assessment("O(n)", "O(n!)")["time_score"] == 0.0
    assert time_complexity_assessment("O(1)", "O(n!)")["time_score"] == 0.0


def test_last_stone_bubble_sort_is_penalized_against_its_n_log_n_target():
    # O(n log n) is rank 5, leaving five worse ranks.  O(n^3) is two ranks
    # slower, so it retains 15/25 internally, displayed as 18/30 in the UI.
    assessment = time_complexity_assessment("O(n log n)", "O(n^3)")
    assert assessment["time_score"] == 15.0
    assert round(assessment["time_score"] * 30 / 25, 1) == 18.0


def test_polynomial_complexities_above_cubic_share_rank_eight():
    assert normalize_complexity("O(n^4)") == "O(n^4+)"
    assert normalize_complexity("O(n^7)") == "O(n^4+)"
    assert complexity_rank("O(n^4)") == 8
    assert complexity_rank("O(n^4)") == complexity_rank("O(n^6)")
    assert time_complexity_assessment("O(n)", "O(n^4)")["time_score"] == 8.333


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
    assert assessment["space_score"] == 16.667
    assert assessment["score_percent"] == 66.668


def test_fixed_character_alphabet_space_complexity_is_scoreable():
    assessment = space_complexity_assessment("O(n)", r"O(|\Sigma|)")
    assert assessment["student_space_complexity"] == "O(1)"
    assert assessment["space_score"] == 25.0
    assert assessment["status"] == "SCORED"


def test_rank_is_one_based_and_better_than_target_is_flagged_for_review():
    assert complexity_rank("O(1)") == 1
    assert complexity_rank("O(n)") == 4
    assert complexity_rank("O(n^4)") == 8
    assert complexity_rank("O(2^n)") == 9
    assert complexity_rank("O(n!)") == 10

    private = private_time_complexity_breakdown("O(n)", "O(log n)")
    assert private["time_score"] == 25.0
    assert private["benchmark_review_required"] is True


def test_curated_additive_benchmark_is_ranked_without_rewriting_student_notation():
    assessment = time_complexity_assessment("O(V + E)", "O(V^2)")
    assert assessment["status"] == "SCORED"
    assert assessment["classification"] == "MODERATE"
    assert assessment["time_score"] == 16.667
    assert assessment["student_time_complexity"] == "O(V^2)"


def test_curated_multivariable_benchmark_uses_private_rank_without_rewriting_report():
    # A public bank target can use rich notation while the student report keeps
    # the analyzer's exact notation.  The student-side O(L) estimate is one
    # input scale, so it can be scored against the benchmark's private bucket.
    assessment = time_complexity_assessment("O(n*k)", "O(L)")
    assert assessment["student_time_complexity"] == "O(L)"
    assert assessment["status"] == "SCORED"
    assert assessment["classification"] == "OPTIMAL"
    assert assessment["time_score"] == 25.0

    # The same multi-dimensional syntax from a student remains intentionally
    # review-only.  We do not guess how independent input dimensions relate.
    student_multi = time_complexity_assessment("O(n*k)", "O(M*N)")
    assert student_multi["status"] == "REVIEW_REQUIRED"


def test_bounded_parameter_complexities_keep_exact_display_but_score_on_n_rank():
    constraints = ["1 <= k <= 100", "1 <= n <= 1000"]
    result = time_complexity_assessment(
        "O(n·k)",
        "O(k*n^2)",
        bounded_parameters={"k"},
    )
    assert result["student_time_complexity"] == "O(n^2*k)"
    assert result["status"] == "SCORED"
    assert result["time_score"] == 16.667

    space = space_complexity_assessment(
        "O(k)",
        "O(n*k)",
        bounded_parameters={"k"},
    )
    assert space["student_space_complexity"] == "O(n*k)"
    assert space["status"] == "SCORED"
    assert space["space_score"] == 16.667

    assert bounded_parameters_from_constraints(constraints) == {"k"}


def test_bounded_single_symbol_stays_constant_for_private_scoring():
    result = time_complexity_assessment(
        "O(k)",
        "O(k)",
        bounded_parameters={"k"},
    )
    assert result["status"] == "SCORED"
    assert result["time_score"] == 25.0


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
                    "status": "ANALYZED", "confidence": 1.0,
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
                    "status": "ANALYZED", "confidence": 1.0,
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
