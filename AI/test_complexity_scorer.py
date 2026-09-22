from scoring.complexity_scorer import (
    calculate_complexity_component_score,
    calculate_complexity_score
)


print("=== Individual Complexity Tests ===")

tests = [
    ("O(n)", "O(n)", 100.0),
    ("O(n^2)", "O(n)", 100.0),
    ("O(n)", "O(n^2)", 60.0),
    ("O(n)", "O(n^3)", 40.0),
    ("O(1)", "O(2^n)", 0.0),
]


for expected, student, expected_score in tests:

    actual_score = calculate_complexity_component_score(
        expected,
        student
    )

    print(
        f"Expected: {expected:8} "
        f"Student: {student:8} "
        f"Score: {actual_score}"
    )

    assert actual_score == expected_score


print("\nAll individual tests passed!")


print("\n=== Time + Space Test ===")

final_score = calculate_complexity_score(
    expected_time="O(n)",
    student_time="O(n^2)",
    expected_space="O(n)",
    student_space="O(n)"
)

print("Expected Final Score: 72.0")
print("Actual Final Score:", final_score)

assert final_score == 72.0

print("\nComplexity scorer test successful!")