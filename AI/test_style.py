from agents.style_agent import analyze_style


problem = """
Given an array of integers, find two numbers that add up to a target.
Return the indices of the two numbers.
"""


code = """
def f(a, t):
    x = {}

    for i, n in enumerate(a):
        c = t - n

        if c in x:
            return [x[c], i]

        x[n] = i

    return []
"""


result = analyze_style(
    problem=problem,
    code=code,
    language="Python"
)


print("Result:")
print(result)

print("\nOverall Style Score:")
print(result.overall_score)

print("\nReadability:")
print(result.readability_score)

print("\nNaming:")
print(result.naming_score)

print("\nMaintainability:")
print(result.maintainability_score)

print("\nDocumentation:")
print(result.documentation_score)

print("\nIssues:")
for issue in result.issues:
    print("-", issue)

print("\nSuggestions:")
for suggestion in result.suggestions:
    print("-", suggestion)

print("\nExplanation:")
print(result.explanation)

print("\nConfidence:")
print(result.confidence)