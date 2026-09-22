import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.complexity_agent import analyze_complexity


with open("evaluation/complexity_tests.json", "r") as file:
    tests = json.load(file)


total = len(tests)
time_correct = 0
space_correct = 0


for test in tests:

    print("\n" + "=" * 60)
    print(test["name"])
    print("=" * 60)

    result = analyze_complexity(
        test["problem"],
        test["code"],
        test["language"]
    )

    predicted_time = result.time_complexity
    predicted_space = result.space_complexity

    print("Expected Time :", test["expected_time"])
    print("Predicted Time:", predicted_time)

    print("Expected Space :", test["expected_space"])
    print("Predicted Space:", predicted_space)

    if predicted_time == test["expected_time"]:
        time_correct += 1

    if predicted_space == test["expected_space"]:
        space_correct += 1


print("\n" + "=" * 60)
print("FINAL RESULTS")
print("=" * 60)

print(f"Time Accuracy  : {time_correct}/{total}")
print(f"Space Accuracy : {space_correct}/{total}")