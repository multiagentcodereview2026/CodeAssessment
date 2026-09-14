from schemas import TestCase, TestResult, ExecutionResult
from scoring.correctness_scorer import calculate_correctness_score


# Test cases
test_cases = [
    TestCase(
        id="TC1",
        input="input 1",
        expected_output="output 1",
        weight=1.0
    ),
    TestCase(
        id="TC2",
        input="input 2",
        expected_output="output 2",
        weight=1.0
    ),
    TestCase(
        id="TC3",
        input="input 3",
        expected_output="output 3",
        weight=1.0
    )
]


# Results from Docker execution
execution_result = ExecutionResult(
    status="ACCEPTED",
    runtime_ms=20,
    memory_kb=12000,
    compile_success=True,
    compile_stderr=None,

    tests_total=3,
    tests_passed=2,
    tests_failed=1,

    results=[
        TestResult(
            test_case_id="TC1",
            status="PASSED",
            runtime_ms=5,
            memory_kb=4000,
            is_hidden=False
        ),

        TestResult(
            test_case_id="TC2",
            status="PASSED",
            runtime_ms=6,
            memory_kb=4000,
            is_hidden=False
        ),

        TestResult(
            test_case_id="TC3",
            status="FAILED",
            runtime_ms=9,
            memory_kb=4000,
            is_hidden=False
        )
    ]
)


# Calculate correctness score
score = calculate_correctness_score(
    execution_result,
    test_cases
)


print("Correctness Score:", score)
print("Expected Score:", 66.67)


# Verify result
assert score == 66.67

print("Correctness scorer test successful!")