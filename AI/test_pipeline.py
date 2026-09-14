from schemas import Problem, TestCase, ExecutionResult, TestResult
from pipeline.assessment_pipeline import assess_submission


# --------------------------------------------------
# 1. Create a sample programming problem
# --------------------------------------------------

problem = Problem(
    problem_id="two_sum_001",
    title="Two Sum",
    description="""
    Given an array of integers and a target value,
    return the indices of two numbers that add up to the target.
    """,
    language="Python",
    expected_time_complexity="O(n)",
    expected_space_complexity="O(n)",
    test_cases=[
        TestCase(
            id="TC1",
            input="[2,7,11,15], 9",
            expected_output="[0,1]",
            weight=1
        ),
        TestCase(
            id="TC2",
            input="[3,2,4], 6",
            expected_output="[1,2]",
            weight=1
        ),
        TestCase(
            id="TC3",
            input="[3,3], 6",
            expected_output="[0,1]",
            weight=2
        )
    ]
)


# --------------------------------------------------
# 2. Student's submitted code
# --------------------------------------------------

student_code = """
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""


# --------------------------------------------------
# 3. Mock Docker execution result
# --------------------------------------------------

execution_result = ExecutionResult(
    status="ACCEPTED",

    runtime_ms=25,
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
            runtime_ms=8,
            memory_kb=4000,
            is_hidden=False,
            input="[2, 7, 11, 15], 9",
            expected_output="[0, 1]",
            actual_output="[0, 1]"
        ),

        TestResult(
            test_case_id="TC2",
            status="PASSED",
            runtime_ms=7,
            memory_kb=4000,
            is_hidden=False,
            input="[3, 2, 4], 6",
            expected_output="[1, 2]",
            actual_output="[1, 2]"
        ),

        TestResult(
            test_case_id="TC3",
            status="FAILED",
            runtime_ms=10,
            memory_kb=4000,
            is_hidden=False,
            input="[3, 3], 6",
            expected_output="[0, 1]",
            actual_output="[]"
        )
    ]
)


# --------------------------------------------------
# 4. Run the complete pipeline
# --------------------------------------------------

result = assess_submission(
    problem=problem,
    code=student_code,
    language="Python",
    execution_result=execution_result
)


# --------------------------------------------------
# 5. Display the result
# --------------------------------------------------

print("========== ASSESSMENT RESULT ==========")

print(
    "Correctness Score:",
    result.scores.correctness
)

print(
    "Complexity Score:",
    result.scores.complexity
)

print(
    "Style Score:",
    result.scores.style
)

print(
    "Originality Score:",
    result.scores.originality
)

print(
    "Final Score:",
    result.scores.final
)

print("\nSimilarity Status:")
print(result.similarity_status)

print("\nCorrectness Explanation:")
print(result.correctness.explanation)

print("\nComplexity Explanation:")
print(result.complexity.explanation)

print("\nStyle Explanation:")
print(result.style.explanation)