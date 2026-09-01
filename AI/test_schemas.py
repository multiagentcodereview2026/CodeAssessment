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
    input="[1, 2, 3], 2",
    expected_output="1",
    actual_output="1",
    passed=True,
    runtime_ms=15,
    memory_kb=12000
)


execution_result = ExecutionResult(
    status="ACCEPTED",
    passed_tests=1,
    failed_tests=0,
    total_tests=1,
    test_results=[test_result],
    runtime_ms=15,
    memory_kb=12000,
    exit_code=0
)


print("Problem:")
print(problem)

print("\nExecution Result:")
print(execution_result)

print("\nSchema test successful!")