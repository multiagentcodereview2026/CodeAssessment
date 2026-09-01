from schemas import ExecutionResult, TestCase


def calculate_correctness_score(
    execution_result: ExecutionResult,
    test_cases: list[TestCase]
) -> float:

    if not test_cases:
        return 0.0

    test_case_map = {
        test_case.id: test_case
        for test_case in test_cases
    }

    weighted_score = 0.0
    total_weight = 0.0

    for result in execution_result.test_results:

        test_case = test_case_map.get(result.test_case_id)

        if test_case is None:
            continue

        total_weight += test_case.weight

        if result.passed:
            weighted_score += test_case.weight

    if total_weight == 0:
        return 0.0

    score = (weighted_score / total_weight) * 100

    return round(score, 2)