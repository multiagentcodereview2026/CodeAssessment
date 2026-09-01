from schemas import ExecutionResult, TestCase, TestResult
from scoring.correctness_scorer import calculate_correctness_score


test_cases = [
    TestCase(
        id="TC1",
        input="input1",
        expected_output="output1",
        weight=1
    ),
    TestCase(
        id="TC2",
        input="input2",
        expected_output="output2",
        weight=1
    ),
    TestCase(
        id="TC3",
        input="input3",
        expected_output="output3",
        weight=2
    ),
    TestCase(
        id="TC4",
        input="input4",
        expected_output="output4",
        weight=2
    )
]


execution_result = ExecutionResult(
    status="WRONG_ANSWER",
    passed_tests=3,
    failed_tests=1,
    total_tests=4,

    test_results=[
        TestResult(
            test_case_id="TC1",
            passed=True
        ),
        TestResult(
            test_case_id="TC2",
            passed=True
        ),
        TestResult(
            test_case_id="TC3",
            passed=False
        ),
        TestResult(
            test_case_id="TC4",
            passed=True
        )
    ]
)


score = calculate_correctness_score(
    execution_result,
    test_cases
)


print("Correctness Score:", score)
print("Expected Score: 66.67")