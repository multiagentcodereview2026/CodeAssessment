from scoring.similarity_scorer import calculate_similarity


# 1. Exact copy
code_a = """
def two_sum(nums, target):
    seen = {}

    for i, num in enumerate(nums):
        complement = target - num

        if complement in seen:
            return [seen[complement], i]

        seen[num] = i

    return []
"""


# 2. Same solution, renamed variables
code_b = """
def find_pair(numbers, value):
    lookup = {}

    for index, number in enumerate(numbers):
        needed = value - number

        if needed in lookup:
            return [lookup[needed], index]

        lookup[number] = index

    return []
"""


# 3. Same problem, but brute-force algorithm
code_c = """
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]

    return []
"""


# 4. Completely different function
code_d = """
def greet(name):
    message = "Hello " + name
    print(message)
    return message
"""


# 5. Another structurally different solution
code_e = """
def find_numbers(values, target):
    result = []

    for i in range(len(values)):
        current = values[i]

        if current == target:
            result.append(i)

    return result
"""


similarities = {
    "Exact copy": calculate_similarity(code_a, code_a),
    "Renamed copy": calculate_similarity(code_a, code_b),
    "Different algorithm": calculate_similarity(code_a, code_c),
    "Unrelated code": calculate_similarity(code_a, code_d),
    "Different structure": calculate_similarity(code_a, code_e),
}


print("=== Similarity Evaluation ===")

for name, score in similarities.items():
    print(f"{name:25} → {score}%")