from schemas import TestCase, Problem, TestResult, ExecutionResult


test_case = TestCase(
    id="TC001",
    input="[1, 2, 3], 2",
    expected_output="1",
    weight=1.0,
    is_hidden=False
)


problem = Problem(
    problem_id="two_sum",
    title="Two Sum",
    description="Find two numbers that add up to the target.",
    language="Python",
    expected_time_complexity="O(n)",
    expected_space_complexity="O(n)",
    test_cases=[test_case]
)


test_result = TestResult(
    test_case_id="TC001",
    status="PASSED",
    input="5",
    expected_output="10",
    actual_output="10",
    runtime_ms=15,
    memory_kb=12000,
    is_hidden=False
)


execution_result = ExecutionResult(
    status="ACCEPTED",
    runtime_ms=15,
    memory_kb=12000,
    compile_success=True,
    compile_stderr=None,
    tests_total=1,
    tests_passed=1,
    tests_failed=0,
    results=[test_result]
)

print("Problem:")
print(problem)

print("\nExecution Result:")
print(execution_result)

print("\nSchema test successful!")