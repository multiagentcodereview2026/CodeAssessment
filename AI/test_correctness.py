from agents.correctness_agent import analyze_correctness


problem = """
Given an array of integers and a target value,
return whether the target exists in the array.
"""


code = """
def contains(arr, target):
  return False
"""


execution_results = """
Test 1:
Input: [1, 2, 3, 4], target=3
Expected: True
Actual: False
Result: FAIL

Test 2:
Input: [1, 2, 3, 4], target=5
Expected: False
Actual: False
Result: PASS

Test 3:
Input: [], target=5
Expected: False
Actual: False
Result: PASS

Test 4:
Input: [10], target=10
Expected: True
Actual: False
Result: FAIL

Total Tests: 4
Passed: 2
Failed: 2
""" 


result = analyze_correctness(
    problem=problem,
    code=code,
    execution_results=execution_results,
    language="Python"
)


print("Result:")
print(result)

print("\nPassed Tests:")
print(result.passed_tests)

print("\nTotal Tests:")
print(result.total_tests)

print("\nCorrectness Score:")
print(result.correctness_score)

print("\nIs Correct:")
print(result.is_correct)

print("\nIssues:")
for issue in result.issues:
    print("-", issue)

print("\nExplanation:")
print(result.explanation)

print("\nConfidence:")
print(result.confidence)