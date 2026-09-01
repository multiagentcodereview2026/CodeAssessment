from agents.complexity_agent import analyze_complexity


problem = """
Given an array of integers, find two numbers that add up to a target.
Return the indices of the two numbers.
"""

code = """
def two_sum(nums, target):
    seen = {}

    for i, num in enumerate(nums):
        complement = target - num

        if complement in seen:
            return [seen[complement], i]

        seen[num] = i

    return []
"""


result = analyze_complexity(
    problem,
    code,
    "Python"
)

print("Result:")
print(result)

print("\nTime Complexity:")
print(result.time_complexity)

print("\nSpace Complexity:")
print(result.space_complexity)

print("\nExplanation:")
print(result.explanation)

print("\nConfidence:")
print(result.confidence)